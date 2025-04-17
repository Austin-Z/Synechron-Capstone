"""
Mermaid directive for Sphinx
===========================

This extension allows you to embed Mermaid diagrams in your documents.

For example::

    .. mermaid::

        sequenceDiagram
            participant Alice
            participant Bob
            Alice->>John: Hello John, how are you?
            loop Healthcheck
                John->>John: Fight against hypochondria
            end
            Note right of John: Rational thoughts <br/>prevail!
            John-->>Alice: Great!
            John->>Bob: How about you?
            Bob-->>John: Jolly good!
"""

import os
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.docutils import SphinxDirective

class mermaid(nodes.General, nodes.Element):
    pass

def html_visit_mermaid_node(self, node):
    self.body.append(self.starttag(node, 'div', CLASS='mermaid'))
    self.body.append(node['code'])
    self.body.append('</div>')
    raise nodes.SkipNode

def setup(app):
    app.add_node(mermaid, html=(html_visit_mermaid_node, None))
    app.add_directive('mermaid', MermaidDirective)
    
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }

class MermaidDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'caption': directives.unchanged,
    }

    def run(self):
        node = mermaid()
        node['code'] = '\n'.join(self.content)
        return [node]
