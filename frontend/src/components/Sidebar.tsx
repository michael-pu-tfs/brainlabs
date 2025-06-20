import { Database, KeyRound, FileText, LineChart, FileEdit, BarChart } from 'lucide-react'
import { cn } from "@/lib/utils"
import { DownloadButton } from './DownloadButton'
import { KeywordMetric, TopicClusterData, ContentSummary, CompetitorRanking, ModifiedContentMetrics } from "@/types/index"

const categories = [
  { name: 'Main', icon: Database },
  { name: 'Keyword', icon: KeyRound },
  { name: 'Topic/AI Cluster', icon: Database },
  { name: 'Competitor Ranking', icon: LineChart },
  { name: 'Outline Summary', icon: FileText },
  { name: 'Modified Content', icon: FileEdit },
  { name: 'Modified Content Metrics', icon: BarChart },
]

interface SidebarProps {
  onCategorySelect: (category: string) => void;
  selectedCategory: string;
  submittedUrl: string | null;
  keywordData: KeywordMetric[];
  topicClusterData: TopicClusterData[];
  contentSummaryData: ContentSummary[];
  competitorRankingData: CompetitorRanking[];
  modifiedContent: (string | number)[];
  modifiedContentMetrics: ModifiedContentMetrics;
}

export function Sidebar({ 
  onCategorySelect, 
  selectedCategory, 
  submittedUrl,
  keywordData,
  topicClusterData,
  contentSummaryData,
  competitorRankingData,
  modifiedContent,
  modifiedContentMetrics
}: SidebarProps) {
  return (
    <div className="fixed w-64 h-full bg-background border-r pt-16">
      <div className="flex flex-col h-full">
        <div className="flex-1 p-4">
          <ul>
            {categories.map((category) => {
              const isDisabled = category.name !== 'Main' && !submittedUrl;
              return (
                <li key={category.name} className="mb-2">
                  <button
                    onClick={() => onCategorySelect(category.name)}
                    disabled={isDisabled}
                    className={cn(
                      "w-full flex items-center p-2 rounded-md",
                      "text-muted-foreground hover:text-foreground",
                      "transition-colors duration-200",
                      "text-sm whitespace-nowrap",
                      selectedCategory === category.name && "bg-muted text-foreground",
                      isDisabled && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    <category.icon className="mr-2 flex-shrink-0" size={20} />
                    <span className="truncate">{category.name}</span>
                  </button>
                </li>
              )}
            )}
          </ul>
        </div>

        {submittedUrl && (
          <div className="p-4 border-t">
            <div className="p-3 bg-muted rounded-lg mb-4">
              <h3 className="text-sm font-medium mb-1">Submitted URL:</h3>
              <p className="text-sm text-muted-foreground break-all">
                {submittedUrl}
              </p>
            </div>
            <DownloadButton 
              category={selectedCategory}
              submittedUrl={submittedUrl}
              variant="outline"
              className="w-full"
              keywordData={keywordData}
              topicClusterData={topicClusterData}
              contentSummaryData={contentSummaryData}
              competitorRankingData={competitorRankingData}
              modifiedContent={modifiedContent}
              modifiedContentMetrics={modifiedContentMetrics}
            />
          </div>
        )}
      </div>
    </div>
  )
}
