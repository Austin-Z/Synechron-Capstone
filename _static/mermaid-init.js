document.addEventListener('DOMContentLoaded', function() {
  // Initialize mermaid with custom configuration
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    securityLevel: 'loose',
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true,
      curve: 'basis'
    },
    sequence: {
      diagramMarginX: 50,
      diagramMarginY: 10,
      actorMargin: 50,
      width: 150,
      height: 65,
      boxMargin: 10,
      boxTextMargin: 5,
      noteMargin: 10,
      messageMargin: 35
    },
    // Support for dark mode
    themeVariables: {
      darkMode: window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    }
  });
});
