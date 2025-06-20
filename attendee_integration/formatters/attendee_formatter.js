// Multi-Format Processor for Attendee Output
// Handles formatting and export of meeting data and actions

class AttendeeFormatter {
  constructor(config = {}) {
    this.config = {
      defaultFormat: 'markdown',
      includeMetadata: true,
      timestampFormat: 'ISO',
      ...config
    };
    this.templates = this.initializeTemplates();
  }

  // Initialize format templates
  initializeTemplates() {
    return {
      markdown: {
        meeting: (data) => this.formatMarkdownMeeting(data),
        actions: (data) => this.formatMarkdownActions(data),
        summary: (data) => this.formatMarkdownSummary(data)
      },
      json: {
        meeting: (data) => JSON.stringify(data, null, 2),
        actions: (data) => JSON.stringify(data.actions, null, 2),
        summary: (data) => JSON.stringify(this.generateSummary(data), null, 2)
      },
      html: {
        meeting: (data) => this.formatHtmlMeeting(data),
        actions: (data) => this.formatHtmlActions(data),
        summary: (data) => this.formatHtmlSummary(data)
      },
      csv: {
        actions: (data) => this.formatCsvActions(data),
        participants: (data) => this.formatCsvParticipants(data)
      },
      txt: {
        meeting: (data) => this.formatPlainTextMeeting(data),
        actions: (data) => this.formatPlainTextActions(data)
      }
    };
  }

  // Main format method
  format(data, format = this.config.defaultFormat, type = 'meeting') {
    try {
      const formatter = this.templates[format]?.[type];
      if (!formatter) {
        throw new Error(`Unsupported format: ${format}/${type}`);
      }
      
      return formatter(data);
    } catch (error) {
      console.error('Formatting error:', error);
      throw error;
    }
  }

  // Markdown formatters
  formatMarkdownMeeting(data) {
    const metadata = this.config.includeMetadata ? this.formatMetadata(data) : '';
    
    return `# ${data.title}

${metadata}

## Participants
${data.participants.map(p => `- ${p}`).join('\n')}

## Transcription
${data.transcription}

## Action Items
${this.formatMarkdownActions(data)}

## Summary
${this.generateSummary(data).text}
`;
  }

  formatMarkdownActions(data) {
    if (!data.actions || data.actions.length === 0) {
      return 'No action items identified.';
    }
    
    return data.actions.map(action => 
      `### ${action.text}
- **Assignee:** ${action.assignee}
- **Priority:** ${action.priority.toUpperCase()}
- **Deadline:** ${action.deadline}
- **Status:** ${action.status || 'pending'}
`).join('\n');
  }

  formatMarkdownSummary(data) {
    const summary = this.generateSummary(data);
    return `# Meeting Summary: ${data.title}

**Duration:** ${data.duration}  
**Date:** ${data.date}  
**Participants:** ${data.participants.length}

## Key Points
${summary.keyPoints.map(point => `- ${point}`).join('\n')}

## Decisions Made
${summary.decisions.map(decision => `- ${decision}`).join('\n')}

## Next Steps
${summary.nextSteps.map(step => `- ${step}`).join('\n')}
`;
  }

  // HTML formatters
  formatHtmlMeeting(data) {
    const metadata = this.config.includeMetadata ? this.formatHtmlMetadata(data) : '';
    
    return `<!DOCTYPE html>
<html>
<head>
    <title>${data.title}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metadata { background: #f5f5f5; padding: 10px; border-radius: 5px; }
        .action-item { border-left: 3px solid #007acc; padding-left: 10px; margin: 10px 0; }
        .priority-high { border-left-color: #ff4444; }
        .priority-medium { border-left-color: #ffaa00; }
        .priority-low { border-left-color: #44ff44; }
    </style>
</head>
<body>
    <h1>${data.title}</h1>
    ${metadata}
    
    <h2>Participants</h2>
    <ul>
        ${data.participants.map(p => `<li>${p}</li>`).join('')}
    </ul>
    
    <h2>Transcription</h2>
    <p>${data.transcription}</p>
    
    <h2>Action Items</h2>
    ${this.formatHtmlActions(data)}
</body>
</html>`;
  }

  formatHtmlActions(data) {
    if (!data.actions || data.actions.length === 0) {
      return '<p>No action items identified.</p>';
    }
    
    return data.actions.map(action => 
      `<div class="action-item priority-${action.priority}">
        <h3>${action.text}</h3>
        <p><strong>Assignee:</strong> ${action.assignee}</p>
        <p><strong>Priority:</strong> ${action.priority.toUpperCase()}</p>
        <p><strong>Deadline:</strong> ${action.deadline}</p>
        <p><strong>Status:</strong> ${action.status || 'pending'}</p>
      </div>`
    ).join('');
  }

  formatHtmlSummary(data) {
    const summary = this.generateSummary(data);
    return `<div class="summary">
      <h2>Meeting Summary</h2>
      <p><strong>Duration:</strong> ${data.duration}</p>
      <p><strong>Date:</strong> ${data.date}</p>
      <p><strong>Participants:</strong> ${data.participants.length}</p>
      
      <h3>Key Points</h3>
      <ul>${summary.keyPoints.map(point => `<li>${point}</li>`).join('')}</ul>
      
      <h3>Decisions Made</h3>
      <ul>${summary.decisions.map(decision => `<li>${decision}</li>`).join('')}</ul>
      
      <h3>Next Steps</h3>
      <ul>${summary.nextSteps.map(step => `<li>${step}</li>`).join('')}</ul>
    </div>`;
  }

  // CSV formatters
  formatCsvActions(data) {
    if (!data.actions || data.actions.length === 0) {
      return 'No action items to export';
    }
    
    const headers = ['Text', 'Assignee', 'Priority', 'Deadline', 'Status'];
    const rows = data.actions.map(action => [
      `"${action.text}"`,
      `"${action.assignee}"`,
      action.priority,
      action.deadline,
      action.status || 'pending'
    ]);
    
    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
  }

  formatCsvParticipants(data) {
    const headers = ['Name', 'Role', 'Email'];
    const rows = data.participants.map(participant => [
      `"${participant}"`,
      'Participant',
      '' // Email would be added if available
    ]);
    
    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
  }

  // Plain text formatters
  formatPlainTextMeeting(data) {
    return `MEETING: ${data.title}
DATE: ${data.date}
DURATION: ${data.duration}

PARTICIPANTS:
${data.participants.map(p => `- ${p}`).join('\n')}

TRANSCRIPTION:
${data.transcription}

ACTION ITEMS:
${this.formatPlainTextActions(data)}
`;
  }

  formatPlainTextActions(data) {
    if (!data.actions || data.actions.length === 0) {
      return 'No action items identified.';
    }
    
    return data.actions.map((action, index) => 
      `${index + 1}. ${action.text}
   Assignee: ${action.assignee}
   Priority: ${action.priority.toUpperCase()}
   Deadline: ${action.deadline}
   Status: ${action.status || 'pending'}
`).join('\n');
  }

  // Utility methods
  formatMetadata(data) {
    return `**Date:** ${data.date}  
**Duration:** ${data.duration}  
**Participants:** ${data.participants.length}  
**Status:** ${data.status}  
**Generated:** ${new Date().toISOString()}
`;
  }

  formatHtmlMetadata(data) {
    return `<div class="metadata">
      <p><strong>Date:</strong> ${data.date}</p>
      <p><strong>Duration:</strong> ${data.duration}</p>
      <p><strong>Participants:</strong> ${data.participants.length}</p>
      <p><strong>Status:</strong> ${data.status}</p>
      <p><strong>Generated:</strong> ${new Date().toISOString()}</p>
    </div>`;
  }

  generateSummary(data) {
    // Simple summary generation (would be enhanced with AI)
    return {
      text: `Meeting "${data.title}" completed with ${data.participants.length} participants. ${data.actions?.length || 0} action items identified.`,
      keyPoints: [
        'Sprint planning discussion',
        'Task allocation completed',
        'Timeline established'
      ],
      decisions: [
        'Proceed with current sprint goals',
        'Assign tasks as discussed'
      ],
      nextSteps: data.actions?.map(action => action.text) || []
    };
  }

  // Export methods
  exportToFile(data, format, type, filename) {
    const content = this.format(data, format, type);
    const blob = new Blob([content], { type: this.getMimeType(format) });
    
    // In browser environment
    if (typeof window !== 'undefined') {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `meeting_${data.id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    }
    
    return content;
  }

  getMimeType(format) {
    const mimeTypes = {
      markdown: 'text/markdown',
      json: 'application/json',
      html: 'text/html',
      csv: 'text/csv',
      txt: 'text/plain'
    };
    return mimeTypes[format] || 'text/plain';
  }
}

module.exports = AttendeeFormatter;

