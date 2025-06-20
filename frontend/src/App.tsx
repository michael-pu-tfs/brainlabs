import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import LoginPage from './app/login/page'
import RegisterPage from './app/register/page'
import { useState, useEffect } from 'react'
// import { Input } from "@/components/ui/input"
// import { Button } from "@/components/ui/button"
// import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Sidebar } from '@/components/Sidebar'
import { Navbar } from '@/components/Navbar'
import {  FormData, KeywordMetric, TopicClusterResponse, TopicClusterData, CompetitorRanking, ContentSummary, ModifiedContentMetrics } from '@/types/index'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { DataTable } from '@/components/DataTable'
import { MainForm } from '@/components/MainForm'
import { API_BASE_URL } from '@/config'

function App() {
  const [theme, setTheme] = useState(() => {
    // Check if there's a saved theme preference in localStorage
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      return savedTheme
    }
    // If no saved preference, default to light
    return 'light'
  });

  useEffect(() => {
    // Update the class and save the preference
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  // const [products] = useState<Product[]>([
  //   {
  //     id: 1,
  //     title: "Classic T-Shirt",
  //     description: "A comfortable and versatile cotton t-shirt for everyday wear.",
  //     price: 19.99,
  //     image: "https://picsum.photos/seed/tshirt/300/200",
  //     category: "Clothing"
  //   },
  //   {
  //     id: 2,
  //     title: "Leather Watch",
  //     description: "Elegant leather strap watch with a minimalist design.",
  //     price: 89.99,
  //     image: "https://picsum.photos/seed/watch/300/200",
  //     category: "Accessories"
  //   },
  //   {
  //     id: 3,
  //     title: "Wireless Earbuds",
  //     description: "High-quality wireless earbuds with noise cancellation.",
  //     price: 129.99,
  //     image: "https://picsum.photos/seed/earbuds/300/200",
  //     category: "Electronics"
  //   },
  //   {
  //     id: 4,
  //     title: "Denim Jeans",
  //     description: "Classic blue denim jeans with a comfortable fit.",
  //     price: 59.99,
  //     image: "https://picsum.photos/seed/jeans/300/200",
  //     category: "Clothing"
  //   },
  //   {
  //     id: 5,
  //     title: "Sunglasses",
  //     description: "Stylish sunglasses with UV protection.",
  //     price: 39.99,
  //     image: "https://picsum.photos/seed/sunglasses/300/200",
  //     category: "Accessories"
  //   },
  //   {
  //     id: 6,
  //     title: "Smartphone",
  //     description: "Latest model smartphone with advanced features.",
  //     price: 699.99,
  //     image: "https://picsum.photos/seed/smartphone/300/200",
  //     category: "Electronics"
  //   },
  //   {
  //     id: 7,
  //     title: "Hooded Sweatshirt",
  //     description: "Warm and cozy hooded sweatshirt for chilly days.",
  //     price: 49.99,
  //     image: "https://picsum.photos/seed/hoodie/300/200",
  //     category: "Clothing"
  //   },
  //   {
  //     id: 8,
  //     title: "Backpack",
  //     description: "Durable and spacious backpack for everyday use.",
  //     price: 79.99,
  //     image: "https://picsum.photos/seed/backpack/300/200",
  //     category: "Accessories"
  //   },
  //   {
  //     id: 9,
  //     title: "Bluetooth Speaker",
  //     description: "Portable Bluetooth speaker with excellent sound quality.",
  //     price: 89.99,
  //     image: "https://picsum.photos/seed/speaker/300/200",
  //     category: "Electronics"
  //   }
  // ])
  // const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('Main')
  const [submittedUrl, setSubmittedUrl] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [keywordData, setKeywordData] = useState<KeywordMetric[]>([])
  const [topicClusterData, setTopicClusterData] = useState<TopicClusterData[]>([])
  const [contentSummaryData, setContentSummaryData] = useState<ContentSummary[]>([])
  const [competitorRankingData, setCompetitorRankingData] = useState<CompetitorRanking[]>([])
  const [modifiedContent, setModifiedContent] = useState<(string | number)[]>([])
  const [modifiedContentMetrics, setModifiedContentMetrics] = useState<ModifiedContentMetrics>({
    url_slug: {},
    content_length_original: {},
    content_length_modified: {},
    keyword_count_original: {},
    keyword_count_modified: {},
    keyword_density_original: {},
    keyword_density_modified: {},
    keywords_incorporated: {},
    outline_count_original: {},
    outline_count_modified: {},
    outlines_incorporated: {}
  })

 

  const processTopicClusterData = (data: TopicClusterResponse) => {
    const processedData: TopicClusterData[] = [];
    
    // Get the number of entries from any of the objects
    const numEntries = Object.keys(data.keyword).length;
    
    for (let i = 0; i < numEntries; i++) {
      processedData.push({
        keyword: data.keyword[i] || '',
        targetTopic: data.topic[i] || '',
        subtopics: data.subtopic[i] || '-',
        clustering: `Cluster ${data.cluster_id[i] || 0}`
      });
    }
    
    return processedData;
  };

  const handleMainFormSubmit = async (formData: FormData) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/process_row`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: formData.url }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      console.log('API Response:', data);
      
      // Set keyword metrics data
      setKeywordData(data.keyword_metrics);
      
      // Process and set topic cluster data
      const processedTopicData = processTopicClusterData(data.topic_ai_cluster);
      setTopicClusterData(processedTopicData);

      // Set competitor ranking data
      setCompetitorRankingData(data.competitor_ranking);

      // Set content summary data
      setContentSummaryData(data.content_summary);

      // Set modified content data
      setModifiedContent(data.modified_content);

      // Set modified content metrics
      setModifiedContentMetrics(data.modified_content_metrics);
      
      setSubmittedUrl(formData.url);
      setSelectedCategory('Keyword');
    } catch (error) {
      console.error('Error:', error);
      alert('Not enough keywords. Please try again or try with different url.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GoogleOAuthProvider clientId="your-google-client-id">
      <Router>
        <Routes>
          <Route 
            path="/login" 
            element={
              localStorage.getItem("isAuthenticated") === "true" 
                ? <Navigate to="/" replace /> 
                : <LoginPage />
            } 
          />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div className="flex min-h-screen bg-background text-foreground">
                  <Sidebar 
                    onCategorySelect={setSelectedCategory}
                    selectedCategory={selectedCategory}
                    submittedUrl={submittedUrl}
                    keywordData={keywordData}
                    topicClusterData={topicClusterData}
                    contentSummaryData={contentSummaryData}
                    competitorRankingData={competitorRankingData}
                    modifiedContent={modifiedContent}
                    modifiedContentMetrics={modifiedContentMetrics}
                  />
                  <div className="flex-1 flex flex-col pl-64">
                    <Navbar 
                      theme={theme} 
                      toggleTheme={toggleTheme}
                    />
                    <main className="flex-1 p-4 mt-16">
                      {selectedCategory === 'Main' ? (
                        <MainForm onSubmit={handleMainFormSubmit} isLoading={isLoading} />
                      ) : (
                        <DataTable 
                          category={selectedCategory} 
                          submittedUrl={submittedUrl} 
                          keywordData={keywordData}
                          topicClusterData={topicClusterData}
                          competitorRankingData={competitorRankingData}
                          contentSummaryData={contentSummaryData}
                          modifiedContent={modifiedContent}
                          modifiedContentMetrics={modifiedContentMetrics}
                        />
                      )}
                    </main>
                  </div>
                </div>
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </GoogleOAuthProvider>
  )
}

export default App
