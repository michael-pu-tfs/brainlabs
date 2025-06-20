// export interface Product {
//   id: number;
//   title: string;
//   description: string;
//   price: number;
//   image: string;
//   category: string;
// }

// export interface FormData {
//   topic: string;
//   audience: string;
//   customerJourney: string;
//   url: string;
//   format: string;
//   type: string;
// }

// export interface KeywordMetric {
//   cpc: number | null;
//   difficulty: number | null;
//   intent_classification: string;
//   keyword: string;
//   position: number;
//   search_volume: number;
//   serp_feature: string[];
//   tf_url: string;
// }

// export interface TopicClusterResponse {
//   cluster_id: { [key: string]: number };
//   keyword: { [key: string]: string };
//   subtopic: { [key: string]: string };
//   topic: { [key: string]: string };
// }

// export interface ApiResponse {
//   keyword_metrics: KeywordMetric[];
//   topic_ai_cluster: TopicClusterResponse;
// }

// export interface TopicClusterData {
//   keyword: string;
//   targetTopic: string;
//   subtopics: string;
//   clustering: string;
// }

// export interface CompetitorRanking {
//   keyword: string;
//   target_url: string;
//   target_rank: string | number;
//   competitor1_url: string;
//   competitor1_rank: number;
//   competitor2_url: string;
//   competitor2_rank: number;
//   competitor3_url: string;
//   competitor3_rank: number;
// }

// export interface ContentSummary {
//   count: string;
//   is_synonym: string;
//   outline: string;
//   parent_keyword: string;
//   priority: string;
//   tag_type: string;
//   tf_url: string;
//   url_slug: string;
// }

// export interface ModifiedContentMetrics {
//   url_slug: { [key: string]: string };
//   content_length_original: { [key: string]: string };
//   content_length_modified: { [key: string]: string };
//   keyword_count_original: { [key: string]: string };
//   keyword_count_modified: { [key: string]: string };
//   keyword_density_original: { [key: string]: string };
//   keyword_density_modified: { [key: string]: string };
//   keywords_incorporated: { [key: string]: string };
//   outline_count_original: { [key: string]: string };
//   outline_count_modified: { [key: string]: string };
//   outlines_incorporated: { [key: string]: string };
// } 


export interface Product {
  id: number;
  title: string;
  description: string;
  price: number;
  image: string;
  category: string;
}

export interface FormData {
  topic: string;
  audience: string;
  customerJourney: string;
  url: string;
  format: string;
  type: string;
}

export interface KeywordMetric {
  cpc: number | null;
  difficulty: number | null;
  intent_classification: string;
  keyword: string;
  position: number;
  search_volume: number;
  serp_feature: string[];
  tf_url: string;
}

export interface TopicClusterResponse {
  cluster_id: { [key: string]: number };
  keyword: { [key: string]: string };
  subtopic: { [key: string]: string };
  topic: { [key: string]: string };
}

export interface ApiResponse {
  keyword_metrics: KeywordMetric[];
  topic_ai_cluster: TopicClusterResponse;
}

export interface TopicClusterData {
  keyword: string;
  targetTopic: string;
  subtopics: string;
  clustering: string;
}

export interface CompetitorRanking {
  keyword: string;
  target_url: string;
  target_rank: string | number;
  competitor1_url: string;
  competitor1_rank: number;
  competitor2_url: string;
  competitor2_rank: number;
  competitor3_url: string;
  competitor3_rank: number;
  tf_url: string;
  tf_rank: number | 'NA';
}

export interface ContentSummary {
  count: string;
  is_synonym: string;
  outline: string;
  parent_keyword: string;
  priority: string;
  tag_type: string;
  tf_url: string;
  url_slug: string;
}

export interface ModifiedContentMetrics {
  url_slug: { [key: string]: string };
  content_length_original: { [key: string]: string };
  content_length_modified: { [key: string]: string };
  keyword_count_original: { [key: string]: string };
  keyword_count_modified: { [key: string]: string };
  keyword_density_original: { [key: string]: string };
  keyword_density_modified: { [key: string]: string };
  keywords_incorporated: { [key: string]: string };
  outline_count_original: { [key: string]: string };
  outline_count_modified: { [key: string]: string };
  outlines_incorporated: { [key: string]: string };
} 