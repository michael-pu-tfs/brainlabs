import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { useState } from 'react';
import { Button } from "@/components/ui/button";

import {
  ArrowUpDown,
  Filter,
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
}
from "@/components/ui/dropdown-menu"
import { KeywordMetric, TopicClusterData, ContentSummary, CompetitorRanking, ModifiedContentMetrics } from "@/types/index"
// import { KeywordMetric } from "@/types/index"

interface DataTableProps {
  category: string;
  submittedUrl: string | null;
  keywordData: KeywordMetric[];
  topicClusterData: TopicClusterData[];
  contentSummaryData: ContentSummary[];
  competitorRankingData: CompetitorRanking[];
  modifiedContent: (string | number)[];
  modifiedContentMetrics: ModifiedContentMetrics;
}

const stripHtmlTags = (html: string) => {
  if (typeof html !== 'string') return html;
  return html
    .replace(/<[^>]*>/g, '') // Remove HTML tags
    .replace(/&nbsp;/g, ' ') // Replace &nbsp; with spaces
    .replace(/&amp;/g, '&') // Replace &amp; with &
    .replace(/&lt;/g, '<') // Replace &lt; with <
    .replace(/&gt;/g, '>') // Replace &gt; with >
    .replace(/&quot;/g, '"') // Replace &quot; with "
    .replace(/&#39;/g, "'"); // Replace &#39; with '
};

const FilterableColumnHeader = ({ 
  title, 
  onSort, 
  onFilter,
  filterValues,
  selectedFilters,
  sortDirection 
}: { 
  title: string;
  onSort: () => void;
  onFilter: (value: string) => void;
  filterValues: string[];
  selectedFilters: string[];
  sortDirection: 'asc' | 'desc' | null;
}) => {
  return (
    <TableHead>
      <div className="flex items-center gap-2">
        {title}
        <div className="flex items-center">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onSort}
            className={cn(sortDirection && "text-primary")}
          >
            <ArrowUpDown className="h-4 w-4" />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm"
                className={cn(
                  selectedFilters.length > 0 && "text-primary"
                )}
              >
                <Filter className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[200px]">
              <div className="max-h-[300px] overflow-auto">
                {filterValues.map((value) => (
                  <DropdownMenuCheckboxItem
                    key={value}
                    checked={selectedFilters.includes(value)}
                    onCheckedChange={() => onFilter(value)}
                  >
                    {value}
                  </DropdownMenuCheckboxItem>
                ))}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </TableHead>
  );
};

const sortData = (a: any, b: any, column: string, direction: 'asc' | 'desc' | null) => {
  if (!direction) return 0;
  
  const aValue = a[column];
  const bValue = b[column];

  // Handle null/undefined values
  if (aValue == null) return direction === 'asc' ? -1 : 1;
  if (bValue == null) return direction === 'asc' ? 1 : -1;

  // Handle numbers
  if (typeof aValue === 'number' && typeof bValue === 'number') {
    return direction === 'asc' ? aValue - bValue : bValue - aValue;
  }

  // Handle strings
  const aString = String(aValue).toLowerCase();
  const bString = String(bValue).toLowerCase();
  
  return direction === 'asc' 
    ? aString.localeCompare(bString)
    : bString.localeCompare(aString);
};

export function DataTable({ 
  category, 
  submittedUrl, 
  keywordData, 
  topicClusterData,
  contentSummaryData,
  competitorRankingData,
  modifiedContent,
  modifiedContentMetrics
}: DataTableProps) {
  const [sortConfig, setSortConfig] = useState<{
    column: string | null;
    direction: 'asc' | 'desc' | null;
  }>({ column: null, direction: null });
  
  const [columnFilters, setColumnFilters] = useState<{
    [column: string]: string[];
  }>({});

  const handleSort = (column: string) => {
    setSortConfig(prev => ({
      column,
      direction: 
        prev.column !== column ? 'asc' :
        prev.direction === null ? 'asc' :
        prev.direction === 'asc' ? 'desc' : null
    }));
  };

  const handleFilter = (column: string, value: string) => {
    setColumnFilters(prev => {
      const filters = { ...prev };
      if (!filters[column]) {
        filters[column] = [value];
      } else if (filters[column].includes(value)) {
        filters[column] = filters[column].filter(v => v !== value);
        if (filters[column].length === 0) {
          delete filters[column];
        }
      } else {
        filters[column] = [...filters[column], value];
      }
      return filters;
    });
  };

  // Function to extract keywords from the modifiedContentMetrics structure
  const extractKeywords = () => {
    if (!modifiedContentMetrics || !modifiedContentMetrics.keywords_incorporated || 
        !modifiedContentMetrics.keywords_incorporated[0]) {
      return [];
    }

    try {
      // Extract the string from keywords_incorporated[0]
      const keywordsString = modifiedContentMetrics.keywords_incorporated[0];
      
      // Parse the comma-separated string of quoted keywords
      const keywordMatches = keywordsString.match(/'([^']+)'/g);
      
      if (!keywordMatches) return [];
      
      // Remove the surrounding quotes
      return keywordMatches.map(match => match.replace(/^'|'$/g, ''));
    } catch (error) {
      console.error("Error extracting keywords:", error);
      return [];
    }
  };

  // Function to extract outlines from the modifiedContentMetrics structure
  const extractOutlines = () => {
    if (!modifiedContentMetrics || !modifiedContentMetrics.outlines_incorporated || 
        !modifiedContentMetrics.outlines_incorporated[0]) {
      return [];
    }

    try {
      // Extract the string from outlines_incorporated[0]
      const outlinesString = modifiedContentMetrics.outlines_incorporated[0];
      
      // If it's empty, return empty array
      if (!outlinesString.trim()) return [];
      
      // Parse the comma-separated string of quoted outlines (if format is the same as keywords)
      const outlineMatches = outlinesString.match(/'([^']+)'/g);
      
      if (!outlineMatches) {
        // If no matches found but string exists, try splitting by comma
        return outlinesString.split(',').map(item => item.trim()).filter(item => item);
      }
      
      // Remove the surrounding quotes
      return outlineMatches.map(match => match.replace(/^'|'$/g, ''));
    } catch (error) {
      console.error("Error extracting outlines:", error);
      return [];
    }
  };

  // Function to highlight keywords and outlines in text with improved UI styling
  const highlightContent = (text: string) => {
    // First strip HTML tags for safety (assumes you have a helper function)
    let processedText = stripHtmlTags(text);
    const keywords = extractKeywords();
    const outlines = extractOutlines();

    // Highlight keywords with a green background and better styling
    if (keywords.length) {
      // Sort keywords by length in descending order to avoid partial matching issues
      const sortedKeywords = [...keywords].sort((a, b) => b.length - a.length);
      sortedKeywords.forEach(keyword => {
        // Create a regex that respects word boundaries and escapes special characters
        const escapedKeyword = keyword.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const regex = new RegExp(`\\b${escapedKeyword}\\b`, 'gi');
        processedText = processedText.replace(
          regex,
          // Wrap each occurrence in a semantic <mark> tag with custom styling
          // match => `<mark class="bg-green-200 text-green-800 font-bold px-1 rounded">${match}</mark>`
          match => `<mark style="background-color: #f5f5dc;" class="text-green-800 font-bold px-1 rounded">${match}</mark>`

        );
      });
    }

    // Highlight outlines with a red background and similar improved styling
    if (outlines.length) {
      // Sort outlines by length in descending order to prevent partial matches
      const sortedOutlines = [...outlines].sort((a, b) => b.length - a.length);
      sortedOutlines.forEach(outline => {
        const escapedOutline = outline.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const regex = new RegExp(`\\b${escapedOutline}\\b`, 'gi');
        processedText = processedText.replace(
          regex,
          // match => `<mark class="bg-red-200 text-red-800 font-bold px-1 rounded">${match}</mark>`
          match => `<mark style="background-color: #f5f5dc;" class="text-red-800 font-bold px-1 rounded">${match}</mark>`

        );
      });
    }

    return processedText;
  };


  switch (category) {
    case 'Topic/AI Cluster':
      // Get unique values for each column
      const uniqueTopicKeywords = Array.from(new Set(topicClusterData.map(item => item.keyword)));
      const uniqueTargetTopics = Array.from(new Set(topicClusterData.map(item => item.targetTopic)));
      const uniqueSubtopics = Array.from(new Set(topicClusterData.map(item => item.subtopics)));
      const uniqueClustering = Array.from(new Set(topicClusterData.map(item => item.clustering)));
      
      // Filter and sort the data
      const filteredAndSortedTopicData = topicClusterData
        .filter(item => 
          Object.entries(columnFilters).every(([column, values]) => {
            const cellValue = String(item[column as keyof TopicClusterData]);
            return values.length === 0 || values.includes(cellValue);
          })
        )
        .sort((a, b) => {
          if (!sortConfig.column) return 0;
          return sortData(a, b, sortConfig.column, sortConfig.direction);
        });

      return (
        <Table>
          <TableCaption>Topic and AI Cluster Analysis</TableCaption>
          <TableHeader>
            <TableRow>
              <FilterableColumnHeader
                title="Keyword"
                onSort={() => handleSort('keyword')}
                onFilter={(value) => handleFilter('keyword', value)}
                filterValues={uniqueTopicKeywords}
                selectedFilters={columnFilters['keyword'] || []}
                sortDirection={sortConfig.column === 'keyword' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Target Topics"
                onSort={() => handleSort('targetTopic')}
                onFilter={(value) => handleFilter('targetTopic', value)}
                filterValues={uniqueTargetTopics}
                selectedFilters={columnFilters['targetTopic'] || []}
                sortDirection={sortConfig.column === 'targetTopic' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Subtopics"
                onSort={() => handleSort('subtopics')}
                onFilter={(value) => handleFilter('subtopics', value)}
                filterValues={uniqueSubtopics}
                selectedFilters={columnFilters['subtopics'] || []}
                sortDirection={sortConfig.column === 'subtopics' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Contextual Intent Clustering"
                onSort={() => handleSort('clustering')}
                onFilter={(value) => handleFilter('clustering', value)}
                filterValues={uniqueClustering}
                selectedFilters={columnFilters['clustering'] || []}
                sortDirection={sortConfig.column === 'clustering' ? sortConfig.direction : null}
              />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAndSortedTopicData.map((row, index) => (
              <TableRow key={index}>
                <TableCell>{row.keyword}</TableCell>
                <TableCell>{row.targetTopic}</TableCell>
                <TableCell>{row.subtopics}</TableCell>
                <TableCell>{row.clustering}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )

    case 'Keyword':
      // Get unique keywords for filter dropdown
      const uniqueKeywords = Array.from(new Set(keywordData.map(item => item.keyword)));
      
      // Filter and sort the data
      const filteredAndSortedKeywordData = keywordData
        .filter(row => {
          return Object.entries(columnFilters).every(([column, values]) => {
            const cellValue = String(row[column as keyof KeywordMetric]);
            return values.length === 0 || values.includes(cellValue);
          });
        })
        .sort((a, b) => {
          if (!sortConfig.column) return 0;
          return sortData(a, b, sortConfig.column, sortConfig.direction);
        });

      return (
        <div className="space-y-4">
          <Table>
            <TableCaption>Keyword Analysis</TableCaption>
            <TableHeader>
              <TableRow>
                <FilterableColumnHeader
                  title="Keyword"
                  onSort={() => handleSort('keyword')}
                  onFilter={(value) => handleFilter('keyword', value)}
                  filterValues={uniqueKeywords}
                  selectedFilters={columnFilters['keyword'] || []}
                  sortDirection={sortConfig.column === 'keyword' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Search Volume"
                  onSort={() => handleSort('search_volume')}
                  onFilter={(value) => handleFilter('search_volume', value)}
                  filterValues={Array.from(new Set(keywordData.map(row => String(row.search_volume))))}
                  selectedFilters={columnFilters['search_volume'] || []}
                  sortDirection={sortConfig.column === 'search_volume' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Intent Classification"
                  onSort={() => handleSort('intent_classification')}
                  onFilter={(value) => handleFilter('intent_classification', value)}
                  filterValues={Array.from(new Set(keywordData.map(row => row.intent_classification)))}
                  selectedFilters={columnFilters['intent_classification'] || []}
                  sortDirection={sortConfig.column === 'intent_classification' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Position"
                  onSort={() => handleSort('position')}
                  onFilter={(value) => handleFilter('position', value)}
                  filterValues={Array.from(new Set(keywordData.map(row => String(row.position))))}
                  selectedFilters={columnFilters['position'] || []}
                  sortDirection={sortConfig.column === 'position' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="CPC"
                  onSort={() => handleSort('cpc')}
                  onFilter={(value) => handleFilter('cpc', value)}
                  filterValues={Array.from(new Set(keywordData.map(row => String(row.cpc))))}
                  selectedFilters={columnFilters['cpc'] || []}
                  sortDirection={sortConfig.column === 'cpc' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Difficulty"
                  onSort={() => handleSort('difficulty')}
                  onFilter={(value) => handleFilter('difficulty', value)}
                  filterValues={Array.from(new Set(keywordData.map(row => String(row.difficulty))))}
                  selectedFilters={columnFilters['difficulty'] || []}
                  sortDirection={sortConfig.column === 'difficulty' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="SERP Features"
                  onSort={() => handleSort('serp_feature')}
                  onFilter={(value) => handleFilter('serp_feature', value)}
                  filterValues={Array.from(new Set(keywordData.map(row => Array.isArray(row.serp_feature) ? row.serp_feature.join(', ') : row.serp_feature)))}
                  selectedFilters={columnFilters['serp_feature'] || []}
                  sortDirection={sortConfig.column === 'serp_feature' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="TF URL"
                  onSort={() => handleSort('tf_url')}
                  onFilter={(value) => handleFilter('tf_url', value)}
                  filterValues={Array.from(new Set(keywordData.map(row => row.tf_url)))}
                  selectedFilters={columnFilters['tf_url'] || []}
                  sortDirection={sortConfig.column === 'tf_url' ? sortConfig.direction : null}
                />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSortedKeywordData.map((row, index) => (
                <TableRow key={index}>
                  <TableCell>{row.keyword}</TableCell>
                  <TableCell>{row.search_volume}</TableCell>
                  <TableCell>{row.intent_classification}</TableCell>
                  <TableCell>{row.position}</TableCell>
                  <TableCell>${row.cpc}</TableCell>
                  <TableCell>{row.difficulty}</TableCell>
                  <TableCell>{Array.isArray(row.serp_feature) ? row.serp_feature.join(', ') : row.serp_feature}</TableCell>
                  <TableCell>{row.tf_url}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )

    case 'Outline Summary':
      // Get unique values for each column
      const uniqueOutlines = Array.from(new Set(contentSummaryData.map(item => item.outline)));
      const uniqueCounts = Array.from(new Set(contentSummaryData.map(item => item.count)));
      const uniqueTagTypes = Array.from(new Set(contentSummaryData.map(item => item.tag_type)));
      const uniquePriorities = Array.from(new Set(contentSummaryData.map(item => item.priority)));
      const uniqueParentKeywords = Array.from(new Set(contentSummaryData.map(item => item.parent_keyword)));
      const uniqueSynonyms = Array.from(new Set(contentSummaryData.map(item => item.is_synonym)));
      const outlineTfUrls = Array.from(new Set(contentSummaryData.map(item => item.tf_url)));
      
      // Filter and sort the data
      const filteredAndSortedContentSummary = contentSummaryData
        .filter(item => 
          Object.entries(columnFilters).every(([column, values]) => {
            const cellValue = String(item[column as keyof ContentSummary]);
            return values.length === 0 || values.includes(cellValue);
          })
        )
        .sort((a, b) => {
          if (!sortConfig.column) return 0;
          return sortData(a, b, sortConfig.column, sortConfig.direction);
        });

      return (
        <Table>
          <TableCaption>Outline Summary</TableCaption>
          <TableHeader>
            <TableRow>
              <FilterableColumnHeader
                title="Outline"
                onSort={() => handleSort('outline')}
                onFilter={(value) => handleFilter('outline', value)}
                filterValues={uniqueOutlines}
                selectedFilters={columnFilters['outline'] || []}
                sortDirection={sortConfig.column === 'outline' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Count"
                onSort={() => handleSort('count')}
                onFilter={(value) => handleFilter('count', value)}
                filterValues={uniqueCounts}
                selectedFilters={columnFilters['count'] || []}
                sortDirection={sortConfig.column === 'count' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Tag Type"
                onSort={() => handleSort('tag_type')}
                onFilter={(value) => handleFilter('tag_type', value)}
                filterValues={uniqueTagTypes}
                selectedFilters={columnFilters['tag_type'] || []}
                sortDirection={sortConfig.column === 'tag_type' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Priority"
                onSort={() => handleSort('priority')}
                onFilter={(value) => handleFilter('priority', value)}
                filterValues={uniquePriorities}
                selectedFilters={columnFilters['priority'] || []}
                sortDirection={sortConfig.column === 'priority' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Parent Keyword"
                onSort={() => handleSort('parent_keyword')}
                onFilter={(value) => handleFilter('parent_keyword', value)}
                filterValues={uniqueParentKeywords}
                selectedFilters={columnFilters['parent_keyword'] || []}
                sortDirection={sortConfig.column === 'parent_keyword' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="Is Synonym"
                onSort={() => handleSort('is_synonym')}
                onFilter={(value) => handleFilter('is_synonym', value)}
                filterValues={uniqueSynonyms}
                selectedFilters={columnFilters['is_synonym'] || []}
                sortDirection={sortConfig.column === 'is_synonym' ? sortConfig.direction : null}
              />
              <FilterableColumnHeader
                title="TF URL"
                onSort={() => handleSort('tf_url')}
                onFilter={(value) => handleFilter('tf_url', value)}
                filterValues={outlineTfUrls}
                selectedFilters={columnFilters['tf_url'] || []}
                sortDirection={sortConfig.column === 'tf_url' ? sortConfig.direction : null}
              />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAndSortedContentSummary.map((row, index) => (
              <TableRow key={index}>
                <TableCell>{row.outline}</TableCell>
                <TableCell>{row.count}</TableCell>
                <TableCell>{row.tag_type}</TableCell>
                <TableCell>{row.priority}</TableCell>
                <TableCell>{row.parent_keyword}</TableCell>
                <TableCell>{row.is_synonym}</TableCell>
                <TableCell>{row.tf_url}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )

    case 'Competitor Ranking':
      // Get unique values for each column
      const uniqueCompetitorKeywords = Array.from(new Set(competitorRankingData.map(item => item.keyword)));
      const uniqueTargetUrls = Array.from(new Set(competitorRankingData.map(item => item.target_url)));
      const uniqueTargetRanks = Array.from(new Set(competitorRankingData.map(item => String(item.target_rank))));
      const uniqueCompetitor1Urls = Array.from(new Set(competitorRankingData.map(item => item.competitor1_url)));
      const uniqueCompetitor1Ranks = Array.from(new Set(competitorRankingData.map(item => String(item.competitor1_rank))));
      const uniqueCompetitor2Urls = Array.from(new Set(competitorRankingData.map(item => item.competitor2_url)));
      const uniqueCompetitor2Ranks = Array.from(new Set(competitorRankingData.map(item => String(item.competitor2_rank))));
      const uniqueCompetitor3Urls = Array.from(new Set(competitorRankingData.map(item => item.competitor3_url)));
      const uniqueCompetitor3Ranks = Array.from(new Set(competitorRankingData.map(item => String(item.competitor3_rank))));
      const uniqueTfUrls = Array.from(new Set(competitorRankingData.map(item => item.tf_url)));
      const uniqueTfRanks = Array.from(new Set(competitorRankingData.map(item => String(item.tf_rank))));

      // Filter and sort the data
      const filteredAndSortedCompetitorData = competitorRankingData
        .filter(item => 
          Object.entries(columnFilters).every(([column, values]) => {
            const cellValue = String(item[column as keyof CompetitorRanking]);
            return values.length === 0 || values.includes(cellValue);
          })
        )
        .sort((a, b) => {
          if (!sortConfig.column) return 0;
          return sortData(a, b, sortConfig.column, sortConfig.direction);
        });

      return (
        <div className="rounded-md border">
          <Table>
            <TableCaption>Competitor Ranking Analysis</TableCaption>
            <TableHeader>
              <TableRow>
                <FilterableColumnHeader
                  title="Keyword"
                  onSort={() => handleSort('keyword')}
                  onFilter={(value) => handleFilter('keyword', value)}
                  filterValues={uniqueCompetitorKeywords}
                  selectedFilters={columnFilters['keyword'] || []}
                  sortDirection={sortConfig.column === 'keyword' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Target URL"
                  onSort={() => handleSort('target_url')}
                  onFilter={(value) => handleFilter('target_url', value)}
                  filterValues={uniqueTargetUrls}
                  selectedFilters={columnFilters['target_url'] || []}
                  sortDirection={sortConfig.column === 'target_url' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Target Rank"
                  onSort={() => handleSort('target_rank')}
                  onFilter={(value) => handleFilter('target_rank', value)}
                  filterValues={uniqueTargetRanks}
                  selectedFilters={columnFilters['target_rank'] || []}
                  sortDirection={sortConfig.column === 'target_rank' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Competitor 1 URL"
                  onSort={() => handleSort('competitor1_url')}
                  onFilter={(value) => handleFilter('competitor1_url', value)}
                  filterValues={uniqueCompetitor1Urls}
                  selectedFilters={columnFilters['competitor1_url'] || []}
                  sortDirection={sortConfig.column === 'competitor1_url' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Rank"
                  onSort={() => handleSort('competitor1_rank')}
                  onFilter={(value) => handleFilter('competitor1_rank', value)}
                  filterValues={uniqueCompetitor1Ranks}
                  selectedFilters={columnFilters['competitor1_rank'] || []}
                  sortDirection={sortConfig.column === 'competitor1_rank' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Competitor 2 URL"
                  onSort={() => handleSort('competitor2_url')}
                  onFilter={(value) => handleFilter('competitor2_url', value)}
                  filterValues={uniqueCompetitor2Urls}
                  selectedFilters={columnFilters['competitor2_url'] || []}
                  sortDirection={sortConfig.column === 'competitor2_url' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Rank"
                  onSort={() => handleSort('competitor2_rank')}
                  onFilter={(value) => handleFilter('competitor2_rank', value)}
                  filterValues={uniqueCompetitor2Ranks}
                  selectedFilters={columnFilters['competitor2_rank'] || []}
                  sortDirection={sortConfig.column === 'competitor2_rank' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Competitor 3 URL"
                  onSort={() => handleSort('competitor3_url')}
                  onFilter={(value) => handleFilter('competitor3_url', value)}
                  filterValues={uniqueCompetitor3Urls}
                  selectedFilters={columnFilters['competitor3_url'] || []}
                  sortDirection={sortConfig.column === 'competitor3_url' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="Rank"
                  onSort={() => handleSort('competitor3_rank')}
                  onFilter={(value) => handleFilter('competitor3_rank', value)}
                  filterValues={uniqueCompetitor3Ranks}
                  selectedFilters={columnFilters['competitor3_rank'] || []}
                  sortDirection={sortConfig.column === 'competitor3_rank' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="TF URL"
                  onSort={() => handleSort('tf_url')}
                  onFilter={(value) => handleFilter('tf_url', value)}
                  filterValues={uniqueTfUrls}
                  selectedFilters={columnFilters['tf_url'] || []}
                  sortDirection={sortConfig.column === 'tf_url' ? sortConfig.direction : null}
                />
                <FilterableColumnHeader
                  title="TF Rank"
                  onSort={() => handleSort('tf_rank')}
                  onFilter={(value) => handleFilter('tf_rank', value)}
                  filterValues={uniqueTfRanks}
                  selectedFilters={columnFilters['tf_rank'] || []}
                  sortDirection={sortConfig.column === 'tf_rank' ? sortConfig.direction : null}
                />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSortedCompetitorData.map((row, index) => (
                <TableRow key={index}>
                  <TableCell>{row.keyword}</TableCell>
                  <TableCell>{row.target_url}</TableCell>
                  <TableCell className="text-center">
                    {row.target_rank === 'NA' ? (
                      <span className="px-2 py-1 rounded-full text-sm bg-gray-100 text-gray-800">
                        NA
                      </span>
                    ) : (
                      <span className={cn(
                        "px-2 py-1 rounded-full text-sm",
                        Number(row.target_rank) <= 3 ? "bg-green-100 text-green-800" : 
                        Number(row.target_rank) <= 6 ? "bg-yellow-100 text-yellow-800" : 
                        "bg-red-100 text-red-800"
                      )}>
                        {row.target_rank}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>{row.competitor1_url}</TableCell>
                  <TableCell className="text-center">
                    <span className={cn(
                      "px-2 py-1 rounded-full text-sm",
                      row.competitor1_rank <= 3 ? "bg-green-100 text-green-800" : 
                      row.competitor1_rank <= 6 ? "bg-yellow-100 text-yellow-800" : 
                      "bg-red-100 text-red-800"
                    )}>
                      {row.competitor1_rank}
                    </span>
                  </TableCell>
                  <TableCell>{row.competitor2_url}</TableCell>
                  <TableCell className="text-center">
                    <span className={cn(
                      "px-2 py-1 rounded-full text-sm",
                      row.competitor2_rank <= 3 ? "bg-green-100 text-green-800" : 
                      row.competitor2_rank <= 6 ? "bg-yellow-100 text-yellow-800" : 
                      "bg-red-100 text-red-800"
                    )}>
                      {row.competitor2_rank}
                    </span>
                  </TableCell>
                  <TableCell>{row.competitor3_url}</TableCell>
                  <TableCell className="text-center">
                    <span className={cn(
                      "px-2 py-1 rounded-full text-sm",
                      row.competitor3_rank <= 3 ? "bg-green-100 text-green-800" : 
                      row.competitor3_rank <= 6 ? "bg-yellow-100 text-yellow-800" : 
                      "bg-red-100 text-red-800"
                    )}>
                      {row.competitor3_rank}
                    </span>
                  </TableCell>
                  <TableCell>{row.tf_url}</TableCell>
                  <TableCell className="text-center">
                    {row.tf_rank === 'NA' ? (
                      <span className="px-2 py-1 rounded-full text-sm bg-gray-100 text-gray-800">
                        NA
                      </span>
                    ) : (
                      <span className={cn(
                        "px-2 py-1 rounded-full text-sm",
                        Number(row.tf_rank) <= 3 ? "bg-green-100 text-green-800" : 
                        Number(row.tf_rank) <= 6 ? "bg-yellow-100 text-yellow-800" : 
                        "bg-red-100 text-red-800"
                      )}>
                        {row.tf_rank}
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )

    case "Modified Content":
      console.log(modifiedContent, "---=========")
      return (
        <div className="space-y-6">
          {submittedUrl && (
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-medium mb-2">Current URL:</h3>
              <p className="text-sm text-muted-foreground">{submittedUrl}</p>
            </div>
          )}
          

          
          <div className="prose dark:prose-invert max-w-none">
            <div className="whitespace-pre-wrap">
              {Array.isArray(modifiedContent) ? (
                modifiedContent.map((content, index) => (
                  <div key={index} 
                    dangerouslySetInnerHTML={{ 
                      __html: highlightContent(String(content)) 
                    }} 
                  />
                ))
              ) : (
                <div 
                  dangerouslySetInnerHTML={{ 
                    __html: highlightContent(String(modifiedContent)) 
                  }} 
                />
              )}
            </div>
          </div>
        </div>
      );

    case 'Modified Content Metrics':
      const metrics = modifiedContentMetrics;
      const metricsData = Object.keys(metrics.url_slug)
        .map(key => ({
          url: metrics.url_slug[key],
          originalLength: Number(metrics.content_length_original[key]),
          modifiedLength: Number(metrics.content_length_modified[key]),
          keywordCountOriginal: metrics.keyword_count_original[key],
          keywordCountModified: metrics.keyword_count_modified[key],
          keywordDensityOriginal: Number(metrics.keyword_density_original[key]) * 100,
          keywordDensityModified: Number(metrics.keyword_density_modified[key]) * 100,
          keywordsIncorporated: metrics.keywords_incorporated[key],
          outlinesIncorporated: metrics.outlines_incorporated[key],
        }))
        .sort((a, b) => {
          if (!sortConfig.column) return 0;
          return sortData(a, b, sortConfig.column, sortConfig.direction);
        });

      return (
        <div className="rounded-md border">
          <Table>
            <TableCaption>Content Modification Metrics Analysis</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>URL</TableHead>
                <TableHead>Original Length</TableHead>
                <TableHead>Modified Length</TableHead>
                <TableHead>Original Keywords</TableHead>
                <TableHead>Modified Keywords</TableHead>
                <TableHead>Original Density</TableHead>
                <TableHead>Modified Density</TableHead>
                <TableHead>Keywords Added</TableHead>
                <TableHead>Outlines Added</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {metricsData.map((row, index) => (
                <TableRow key={index}>
                  <TableCell>{row.url}</TableCell>
                  <TableCell>{row.originalLength}</TableCell>
                  <TableCell>{row.modifiedLength}</TableCell>
                  <TableCell>{row.keywordCountOriginal}</TableCell>
                  <TableCell>{row.keywordCountModified}</TableCell>
                  <TableCell>{row.keywordDensityOriginal.toFixed(2)}%</TableCell>
                  <TableCell>{row.keywordDensityModified.toFixed(2)}%</TableCell>
                  <TableCell>{row.keywordsIncorporated}</TableCell>
                  <TableCell>{row.outlinesIncorporated}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )

    default:
      return null
  }
} 