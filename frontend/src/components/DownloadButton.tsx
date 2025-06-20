import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"
import * as XLSX from 'xlsx'
import { KeywordMetric, TopicClusterData, ContentSummary, CompetitorRanking, ModifiedContentMetrics } from "@/types/index"

interface DownloadButtonProps {
  category: string;
  submittedUrl: string | null;
  variant?: "default" | "outline";
  className?: string;
  keywordData: KeywordMetric[];
  topicClusterData: TopicClusterData[];
  contentSummaryData: ContentSummary[];
  competitorRankingData: CompetitorRanking[];
  modifiedContent: (string | number)[];
  modifiedContentMetrics: ModifiedContentMetrics;
}

export function DownloadButton({ 
  category, 
  submittedUrl, 
  variant = "default",
  className = "",
  keywordData,
  topicClusterData,
  contentSummaryData,
  competitorRankingData,
  modifiedContent,
  modifiedContentMetrics
}: DownloadButtonProps) {
  const handleDownload = async () => {
    try {
      const workbook = XLSX.utils.book_new();

      // Keywords Sheet
      const keywordsWs = XLSX.utils.json_to_sheet(keywordData.map(row => ({
        Keyword: row.keyword,
        'Search Volume': row.search_volume,
        Intent: row.intent_classification,
        Position: row.position,
        CPC: row.cpc,
        Difficulty: row.difficulty,
        'SERP Features': Array.isArray(row.serp_feature) ? row.serp_feature.join(', ') : row.serp_feature,
        URL: row.tf_url
      })));
      XLSX.utils.book_append_sheet(workbook, keywordsWs, 'Keywords');

      // Topic/AI Cluster Sheet
      const topicClusterWs = XLSX.utils.json_to_sheet(topicClusterData.map(row => ({
        Keyword: row.keyword,
        'Target Topic': row.targetTopic,
        Subtopics: row.subtopics,
        Clustering: row.clustering
      })));
      XLSX.utils.book_append_sheet(workbook, topicClusterWs, 'Topic-AI Cluster');

      // Outline Summary Sheet
      const outlineSummaryWs = XLSX.utils.json_to_sheet(contentSummaryData.map(row => ({
        Outline: row.outline,
        Count: row.count,
        'Tag Type': row.tag_type,
        Priority: row.priority,
        'Parent Keyword': row.parent_keyword,
        'Is Synonym': row.is_synonym,
        'TF URL': row.tf_url,
        'URL Slug': row.url_slug
      })));
      XLSX.utils.book_append_sheet(workbook, outlineSummaryWs, 'Outline Summary');

      // Competitor Ranking Sheet
      const competitorRankingWs = XLSX.utils.json_to_sheet(competitorRankingData.map(row => ({
        Keyword: row.keyword,
        'Target URL': row.target_url,
        'TF Rank':row.tf_rank,
        'Target Rank': row.target_rank,
        'Competitor 1 URL': row.competitor1_url,
        'Competitor 1 Rank': row.competitor1_rank,
        'Competitor 2 URL': row.competitor2_url,
        'Competitor 2 Rank': row.competitor2_rank,
        'Competitor 3 URL': row.competitor3_url,
        'Competitor 3 Rank': row.competitor3_rank,
        'tf_url': row.tf_url
      })));
      XLSX.utils.book_append_sheet(workbook, competitorRankingWs, 'Competitor Ranking');

      // Modified Content Metrics Sheet
      const metricsData = Object.keys(modifiedContentMetrics.url_slug).map(key => ({
        URL: modifiedContentMetrics.url_slug[key],
        'Original Length': modifiedContentMetrics.content_length_original[key],
        'Modified Length': modifiedContentMetrics.content_length_modified[key],
        'Original Keywords': modifiedContentMetrics.keyword_count_original[key],
        'Modified Keywords': modifiedContentMetrics.keyword_count_modified[key],
        'Original Density': `${(Number(modifiedContentMetrics.keyword_density_original[key]) * 100).toFixed(2)}%`,
        'Modified Density': `${(Number(modifiedContentMetrics.keyword_density_modified[key]) * 100).toFixed(2)}%`,
        'Keywords Added': modifiedContentMetrics.keywords_incorporated[key],
        'Outlines Added': modifiedContentMetrics.outlines_incorporated[key]
      }));
      const metricsWs = XLSX.utils.json_to_sheet(metricsData);
      XLSX.utils.book_append_sheet(workbook, metricsWs, 'Content Metrics');

      // Modified Content Sheet
      const modifiedContentWs = XLSX.utils.aoa_to_sheet([
        ['Modified Content'],
        ...modifiedContent.map(content => [content.toString()])
      ]);
      XLSX.utils.book_append_sheet(workbook, modifiedContentWs, 'Modified Content');

      // Generate filename based on category and URL
      const urlSlug = submittedUrl ? new URL(submittedUrl).hostname : 'data';
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `${urlSlug}_${timestamp}_${getFileName(category)}.xlsx`;

      // Write and download the file
      XLSX.writeFile(workbook, filename);
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('Failed to download file. Please try again.');
    }
  };

  return (
    <Button
      onClick={handleDownload}
      variant={variant}
      className={`flex items-center gap-2 ${className}`}
    >
      <Download className="h-4 w-4" />
      Download Report
    </Button>
  );
}

const getFileName = (category: string) => {
  switch (category) {
    case 'Keyword':
      return 'keyword_metrics';
    case 'Topic/AI Cluster':
      return 'topic_cluster';
    case 'Competitor Ranking':
      return 'competitor_ranking';
    case 'Outline Summary':
      return 'outline_summary';
    case 'Modified Content':
      return 'modified_content';
    case 'Modified Content Metrics':
      return 'content_metrics';
    default:
      return 'data';
  }
};