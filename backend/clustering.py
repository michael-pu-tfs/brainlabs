import numpy as np
from sklearn.cluster import DBSCAN
import pandas as pd
import json
from topic_generation import process_row_parallel, extract_topic_subtopic


def calculate_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Calculate pairwise cosine similarity matrix.
    Uses optimized matrix multiplication for speed.
    """
    try:
        # Ensure embeddings are normalized and handle zero vectors
        norms = np.linalg.norm(embeddings, axis=1)
        # Replace zero norms with 1 to avoid division by zero
        norms[norms == 0] = 1
        embeddings_normalized = embeddings / norms[:, np.newaxis]
        # Calculate similarity matrix
        similarity_matrix = np.dot(embeddings_normalized, embeddings_normalized.T)
        # Ensure values are between -1 and 1
        similarity_matrix = np.clip(similarity_matrix, -1, 1)
        return similarity_matrix
    except Exception as e:
        print(f"Error in calculate_similarity_matrix: {str(e)}")
        raise


def safe_eval_embedding(emb):
    """Safely evaluate embedding string or return the original if it's already a list"""
    if isinstance(emb, str):
        try:
            return eval(emb)
        except:
            return []
    return emb if isinstance(emb, (list, np.ndarray)) else []


def cluster_existing_embeddings(
    df: pd.DataFrame,
    keyword_col: str = "keyword",
    embedding_col: str = "embedding",
    min_similarity: float = 0.70,
    min_samples: int = 1,
) -> pd.DataFrame:
    """
    Cluster keywords using existing embeddings from DataFrame.
    """
    try:
        print("Processing embeddings...")
        # Convert embeddings to numpy array safely
        embeddings_list = []
        for emb in df[embedding_col]:
            embedding = np.array(emb) if isinstance(emb, list) else emb
            if isinstance(embedding, np.ndarray) and embedding.size > 0:
                embeddings_list.append(embedding)
            else:
                print(f"Warning: Invalid embedding found, using zeros")
                dim = len(embeddings_list[0]) if embeddings_list else 768
                embeddings_list.append(np.zeros(dim))

        embeddings = np.array(embeddings_list)
        print(f"Embeddings shape: {embeddings.shape}")

        print("Calculating similarity matrix...")
        similarity_matrix = calculate_similarity_matrix(embeddings)

        # Convert similarity to distance and ensure non-negative values
        print("Preparing distance matrix...")
        distance_matrix = 1 - similarity_matrix
        # Ensure all distances are non-negative
        distance_matrix = np.abs(distance_matrix)

        print(f"Distance matrix shape: {distance_matrix.shape}")
        print(f"Distance range: [{distance_matrix.min()}, {distance_matrix.max()}]")

        # Perform clustering
        print("Performing clustering...")
        eps = 1 - min_similarity  # Convert similarity threshold to distance
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed").fit(
            distance_matrix
        )

        # Add cluster labels to DataFrame
        df_with_clusters = df.copy()
        df_with_clusters["cluster_id"] = clustering.labels_

        print(
            f"Number of clusters found: {len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)}"
        )
        return df_with_clusters

    except Exception as e:
        print(f"Error in cluster_existing_embeddings: {str(e)}")
        raise


def analyze_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary DataFrame with cluster statistics.
    """
    try:
        cluster_stats = (
            df.groupby("cluster_id").agg({"keyword": ["count", list]}).reset_index()
        )

        cluster_stats.columns = ["cluster_id", "size", "keywords"]
        cluster_stats["sample_keywords"] = cluster_stats["keywords"].apply(
            lambda x: x[:5]
        )

        # Sort by cluster size descending
        cluster_stats = cluster_stats.sort_values("size", ascending=False)

        return cluster_stats
    except Exception as e:
        print(f"Error in analyze_clusters: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Load the JSON data from the file
        print("Loading embeddings data...")
        with open("./embeddings.json", "r") as json_file:
            embedding_data = json.load(json_file)

        # Convert the loaded data into a pandas DataFrame
        print("Converting data to DataFrame...")
        df = pd.DataFrame(embedding_data)

        # Ensure the embedding column exists
        if "embedding" not in df.columns:
            raise ValueError("No 'embedding' column found in the data")

        print(f"Data loaded successfully. Shape: {df.shape}")

        # Perform clustering
        df_clustered = cluster_existing_embeddings(
            df=df, keyword_col="keyword", embedding_col="embedding", min_similarity=0.85
        )

        # Analyze results
        analysis = analyze_clusters(df_clustered)
        print("\nCluster Analysis:")
        print(analysis.to_string())

        # Save results
        print("\nSaving results...")
        df_clustered.to_csv("clustered_keywords.csv", index=False)
        analysis.to_csv("cluster_analysis.csv", index=False)
        print("Processing completed successfully!")

        ##topic generation
        keywords_list = [",".join(i) for i in analysis["keywords"].tolist()]

        analysis["response"] = process_row_parallel(keywords_list)

        analysis[["Topic", "Subtopic"]] = analysis["response"].apply(
            lambda x: pd.Series(extract_topic_subtopic(x))
        )

        print(analysis)
        topic, subtopic = [], []
        for i, row in df_clustered.iterrows():
            df = analysis[analysis["cluster_id"] == row.cluster_id]
            topic.append(df.iloc[0].Topic)
            subtopic.append(df.iloc[0].Subtopic)
        df_clustered["topic"], df_clustered["subtopic"] = topic, subtopic
        df_clustered = df_clustered[["keyword", "topic", "subtopic", "cluster_id"]]
        print(df_clustered.to_dict())
        # cluster_df.to_csv('biopharma1_topic_subtopic.csv', index=False)

    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        raise
