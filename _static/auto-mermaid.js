document.addEventListener('DOMContentLoaded', function() {
  // Find all pre elements with language-mermaid class
  const mermaidBlocks = document.querySelectorAll('pre.language-mermaid');
  
  // Convert each pre element to a div with class mermaid
  mermaidBlocks.forEach(function(block, index) {
    // Create a new div element
    const mermaidDiv = document.createElement('div');
    mermaidDiv.className = 'mermaid';
    mermaidDiv.id = 'mermaid-diagram-' + index;
    
    // Get the mermaid code from the pre element
    const code = block.textContent;
    mermaidDiv.textContent = code;
    
    // Replace the pre element with the new div
    block.parentNode.replaceChild(mermaidDiv, block);
  });
  
  // Initialize mermaid
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
      flowchart: { useMaxWidth: true }
    });
  } else {
    // Load mermaid if it's not already loaded
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/mermaid@9.1.7/dist/mermaid.min.js';
    script.onload = function() {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
        flowchart: { useMaxWidth: true }
      });
    };
    document.head.appendChild(script);
  }
});
