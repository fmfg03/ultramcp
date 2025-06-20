import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Upload, 
  Mic, 
  FileText, 
  CheckSquare, 
  Clock, 
  User,
  Calendar,
  Send,
  Download,
  Play,
  Pause,
  AlertCircle,
  CheckCircle
} from 'lucide-react'

const meetings = [
  {
    id: 1,
    title: 'Weekly Sprint Planning',
    date: '2025-06-19',
    duration: '45 min',
    participants: ['John Doe', 'Jane Smith', 'Mike Johnson'],
    status: 'processed',
    transcription: 'Meeting focused on sprint goals and task allocation...',
    actions: [
      { id: 1, text: 'Update user authentication system', assignee: 'John Doe', priority: 'high', deadline: '2025-06-25' },
      { id: 2, text: 'Review API documentation', assignee: 'Jane Smith', priority: 'medium', deadline: '2025-06-22' },
      { id: 3, text: 'Prepare demo for client meeting', assignee: 'Mike Johnson', priority: 'high', deadline: '2025-06-21' }
    ]
  },
  {
    id: 2,
    title: 'Product Strategy Review',
    date: '2025-06-18',
    duration: '60 min',
    participants: ['Sarah Wilson', 'Tom Brown', 'Lisa Davis'],
    status: 'processing',
    transcription: 'Discussion about Q3 product roadmap and market analysis...',
    actions: [
      { id: 4, text: 'Conduct competitor analysis', assignee: 'Sarah Wilson', priority: 'medium', deadline: '2025-06-30' },
      { id: 5, text: 'Update product pricing strategy', assignee: 'Tom Brown', priority: 'high', deadline: '2025-06-26' }
    ]
  }
]

const actionItems = meetings.flatMap(m => m.actions)

export function AttendeePanel() {
  const [selectedMeeting, setSelectedMeeting] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isRecording, setIsRecording] = useState(false)
  const [newAction, setNewAction] = useState({
    text: '',
    assignee: '',
    priority: 'medium',
    deadline: ''
  })

  const handleFileUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
      setUploadedFile(file)
    }
  }

  const startRecording = () => {
    setIsRecording(true)
    // Simulate recording
    setTimeout(() => {
      setIsRecording(false)
    }, 5000)
  }

  const processTranscription = () => {
    // Simulate processing
    console.log('Processing transcription...')
  }

  const addAction = () => {
    if (newAction.text && newAction.assignee) {
      // Add action logic here
      setNewAction({
        text: '',
        assignee: '',
        priority: 'medium',
        deadline: ''
      })
    }
  }

  const dispatchToMCP = (actionId) => {
    console.log('Dispatching action to MCP system:', actionId)
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-600'
      case 'medium': return 'bg-yellow-600'
      case 'low': return 'bg-green-600'
      default: return 'bg-gray-600'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'processed': return 'text-green-600'
      case 'processing': return 'text-yellow-600'
      case 'pending': return 'text-gray-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Attendee Panel</h1>
          <p className="text-muted-foreground">Meeting transcription and action item extraction</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="text-green-600">
            <CheckCircle className="w-3 h-3 mr-1" />
            {actionItems.length} Actions Tracked
          </Badge>
        </div>
      </div>

      {/* Upload & Recording Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="w-5 h-5 mr-2" />
              Upload Meeting Recording
            </CardTitle>
            <CardDescription>Upload audio/video files for transcription</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept="audio/*,video/*"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  Click to upload or drag and drop
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  MP3, MP4, WAV, MOV up to 100MB
                </p>
              </label>
            </div>
            
            {uploadedFile && (
              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div className="flex items-center">
                  <FileText className="w-4 h-4 mr-2" />
                  <span className="text-sm">{uploadedFile.name}</span>
                </div>
                <Button size="sm" onClick={processTranscription}>
                  Process
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Mic className="w-5 h-5 mr-2" />
              Live Recording
            </CardTitle>
            <CardDescription>Record meeting audio in real-time</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-center py-8">
              <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-4 ${
                isRecording ? 'bg-red-100 animate-pulse' : 'bg-gray-100'
              }`}>
                <Mic className={`w-8 h-8 ${isRecording ? 'text-red-600' : 'text-muted-foreground'}`} />
              </div>
              <Button
                onClick={startRecording}
                disabled={isRecording}
                className={isRecording ? 'bg-red-600 hover:bg-red-700' : ''}
              >
                {isRecording ? (
                  <>
                    <Pause className="w-4 h-4 mr-2" />
                    Recording... (0:05)
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start Recording
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Meetings List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Calendar className="w-5 h-5 mr-2" />
            Recent Meetings
          </CardTitle>
          <CardDescription>Processed meeting transcriptions and extracted actions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {meetings.map((meeting) => (
              <div 
                key={meeting.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors hover:bg-accent ${
                  selectedMeeting === meeting.id ? 'bg-accent' : ''
                }`}
                onClick={() => setSelectedMeeting(selectedMeeting === meeting.id ? null : meeting.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{meeting.title}</h4>
                    <div className="text-sm text-muted-foreground">
                      {meeting.date} • {meeting.duration} • {meeting.participants.length} participants
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(meeting.status)}>
                      {meeting.status === 'processed' ? (
                        <CheckCircle className="w-3 h-3 mr-1" />
                      ) : (
                        <Clock className="w-3 h-3 mr-1" />
                      )}
                      {meeting.status}
                    </Badge>
                    <Badge variant="outline">
                      {meeting.actions.length} actions
                    </Badge>
                  </div>
                </div>

                {selectedMeeting === meeting.id && (
                  <div className="mt-4 pt-4 border-t space-y-4">
                    <div>
                      <h5 className="font-medium mb-2">Participants</h5>
                      <div className="flex flex-wrap gap-2">
                        {meeting.participants.map((participant) => (
                          <Badge key={participant} variant="secondary">
                            <User className="w-3 h-3 mr-1" />
                            {participant}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h5 className="font-medium mb-2">Transcription Summary</h5>
                      <p className="text-sm text-muted-foreground bg-muted p-3 rounded">
                        {meeting.transcription}
                      </p>
                    </div>

                    <div>
                      <h5 className="font-medium mb-2">Extracted Actions</h5>
                      <div className="space-y-2">
                        {meeting.actions.map((action) => (
                          <div key={action.id} className="flex items-center justify-between p-3 border rounded">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <CheckSquare className="w-4 h-4 text-muted-foreground" />
                                <span className="text-sm">{action.text}</span>
                              </div>
                              <div className="text-xs text-muted-foreground mt-1 ml-6">
                                Assigned to: {action.assignee} • Due: {action.deadline}
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge className={getPriorityColor(action.priority)}>
                                {action.priority}
                              </Badge>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => dispatchToMCP(action.id)}
                              >
                                <Send className="w-3 h-3 mr-1" />
                                Dispatch
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Manual Action Creation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CheckSquare className="w-5 h-5 mr-2" />
            Add Manual Action Item
          </CardTitle>
          <CardDescription>Create action items manually or validate extracted ones</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="lg:col-span-2">
              <label className="text-sm font-medium mb-2 block">Action Description</label>
              <Textarea
                placeholder="Describe the action item..."
                value={newAction.text}
                onChange={(e) => setNewAction({...newAction, text: e.target.value})}
              />
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">Assignee</label>
              <Input
                placeholder="Enter assignee name"
                value={newAction.assignee}
                onChange={(e) => setNewAction({...newAction, assignee: e.target.value})}
              />
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">Priority</label>
              <Select value={newAction.priority} onValueChange={(value) => setNewAction({...newAction, priority: value})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">Deadline</label>
              <Input
                type="date"
                value={newAction.deadline}
                onChange={(e) => setNewAction({...newAction, deadline: e.target.value})}
              />
            </div>
            
            <div className="lg:col-span-2">
              <Button onClick={addAction} className="w-full">
                <CheckSquare className="w-4 h-4 mr-2" />
                Add Action Item
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Items Dashboard */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center">
              <AlertCircle className="w-5 h-5 mr-2" />
              All Action Items ({actionItems.length})
            </span>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {actionItems.map((action) => (
              <div key={action.id} className="flex items-center justify-between p-3 border rounded hover:bg-accent">
                <div className="flex items-center space-x-3">
                  <CheckSquare className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <div className="text-sm font-medium">{action.text}</div>
                    <div className="text-xs text-muted-foreground">
                      {action.assignee} • Due: {action.deadline}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className={getPriorityColor(action.priority)}>
                    {action.priority}
                  </Badge>
                  <Button size="sm" variant="outline">
                    <Send className="w-3 h-3 mr-1" />
                    Auto-dispatch
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

