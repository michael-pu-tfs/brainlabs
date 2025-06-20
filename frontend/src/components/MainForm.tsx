import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select"
import { useState } from "react"
import { Loader2 } from "lucide-react"
import { FormData } from "@/types/index"

interface MainFormProps {
  onSubmit: (data: FormData) => Promise<void>;
  isLoading: boolean;
}

export function MainForm({ onSubmit, isLoading }: MainFormProps) {
  const [formData, setFormData] = useState<FormData>({
    topic: "",
    audience: "",
    customerJourney: "",
    url: "",
    format: "",
    type: "",
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto p-6">
      <div className="space-y-4">
        <div>
          <Label htmlFor="topic">Topic</Label>
          <Input
            id="topic"
            value={formData.topic}
            onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="audience">Audience</Label>
          <Input
            id="audience"
            value={formData.audience}
            onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="customerJourney">Customer Journey</Label>
          <Input
            id="customerJourney"
            value={formData.customerJourney}
            onChange={(e) => setFormData({ ...formData, customerJourney: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="url">
            URL <span className="text-red-500">*</span>
          </Label>
          <Input
            id="url"
            placeholder="Enter URL"
            value={formData.url}
            onChange={(e) => setFormData({ ...formData, url: e.target.value })}
          />
        </div>

        <div>
          <Label htmlFor="format">Format</Label>
          <Select
            value={formData.format}
            onValueChange={(value) => setFormData({ ...formData, format: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select format" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="marketing">Marketing (AEM)</SelectItem>
              <SelectItem value="product">Product</SelectItem>
              <SelectItem value="blog">Blog</SelectItem>
              <SelectItem value="learning">Learning Center</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="type">Type</Label>
          <Select
            value={formData.type}
            onValueChange={(value) => setFormData({ ...formData, type: value })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="new">New Page</SelectItem>
              <SelectItem value="modify">Modify Existing Page</SelectItem>
              <SelectItem value="merge">Merge Pages</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button 
          type="submit" 
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...This can take upto 5-10 minutes...
            </>
          ) : (
            'Submit'
          )}
        </Button>
      </div>
    </form>
  )
} 