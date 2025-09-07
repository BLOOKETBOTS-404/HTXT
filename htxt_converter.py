#!/usr/bin/env python3
"""Simpler HTXT Converter - fixed string handling.
"""
import sys, html, os

INDENT_SPACES = 2

def parse_attributes(s):
    attrs = {}
    parts = []
    cur = ''
    in_quote = False
    quote_char = ''
    for ch in s:
        if ch in ('"', "'"):
            if not in_quote:
                in_quote = True
                quote_char = ch
                cur += ch
            elif quote_char == ch:
                in_quote = False
                cur += ch
            else:
                cur += ch
        elif ch == ' ' and not in_quote:
            if cur.strip():
                parts.append(cur.strip())
                cur = ''
        else:
            cur += ch
    if cur.strip():
        parts.append(cur.strip())
    for p in parts:
        if '=' in p:
            k, v = p.split('=',1)
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            attrs[k.strip()] = v
        else:
            attrs[p] = ""
    return attrs

def tokenize_lines(text):
    lines = text.splitlines()
    tokens = []
    for raw in lines:
        line = raw.rstrip('\n').rstrip('\r')
        if not line.strip():
            continue
        leading = len(line) - len(line.lstrip(' '))
        indent_level = leading // INDENT_SPACES
        content = line.lstrip(' ')
        tokens.append((indent_level, content))
    return tokens

def parse_tokens(tokens):
    root = ('root', {}, None, [], False)
    stack = [(-1, root)]
    for indent, line in tokens:
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith('- '):
            tag = 'text'; attrs = {}; content = line[2:]; self_closing = False
        else:
            if ':' in line:
                left, right = line.split(':',1)
                content = right.lstrip(' ')
            else:
                left = line; content = ''
            if '[' in left and ']' in left:
                tag = left.split('[',1)[0].strip()
                attr_str = left.split('[',1)[1].rsplit(']',1)[0]
                attrs = parse_attributes(attr_str)
            else:
                tag = left.strip(); attrs = {}
            self_closing = False
            if tag.endswith('/'):
                tag = tag[:-1].strip(); self_closing = True
        node = (tag, attrs, content, [], self_closing)
        parent[3].append(node)
        stack.append((indent, node))
    return root

void_elements = set([ 'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'])

def render_node(node, indent=0):
    tag, attrs, content, children, self_closing = node
    pad = '  ' * indent
    if tag == 'root':
        return ''.join(render_node(c, indent) for c in children)
    if tag == 'text':
        return pad + html.escape(content) + '\n'
    if tag == 'page':
        head_html=''; body_html=''
        for c in children:
            if c[0]=='head': head_html += ''.join(render_node(cc, indent+1) for cc in c[3])
            elif c[0]=='body': body_html += ''.join(render_node(cc, indent+1) for cc in c[3])
            else: body_html += render_node(c, indent+1)
        return '<!DOCTYPE html>\n<html>\n  <head>\n' + head_html + '  </head>\n  <body>\n' + body_html + '  </body>\n</html>\n'
    attr_str=''
    for k,v in attrs.items():
        if v=="": attr_str += ' ' + k
        else: attr_str += ' ' + k + '="' + html.escape(v, quote=True) + '"'
    if content.startswith('| '):
        inner = content[2:] + '\n'; inner_raw = True
    else:
        inner = html.escape(content) if content else ''; inner_raw = False
    children_html=''
    if children:
        for c in children: children_html += render_node(c, indent+1)
    if inner_raw:
        return pad + '<' + tag + attr_str + '>\n' + pad + '  ' + inner + children_html + pad + '</' + tag + '>\n'
    else:
        if (tag in void_elements or self_closing) and not children and not inner:
            return pad + '<' + tag + attr_str + ' />\n'
        else:
            inner_combined = (inner + '\n' if inner and not inner.endswith('\n') else inner) + children_html
            inner_combined = inner_combined.rstrip('\n')
            if inner_combined:
                replaced = inner_combined.replace('\n', '\n' + pad + '  ')
                return pad + '<' + tag + attr_str + '>\n' + pad + '  ' + replaced + '\n' + pad + '</' + tag + '>\n'
            else:
                return pad + '<' + tag + attr_str + '></' + tag + '>\n'

def compile_htxt(text):
    tokens = tokenize_lines(text)
    tree = parse_tokens(tokens)
    return render_node(tree)

def main():
    if len(sys.argv) < 2:
        print('Usage: python htxt_converter.py input.htxt [output.html]')
        sys.exit(1)
    inp = sys.argv[1]
    if not os.path.exists(inp):
        print('Input not found:', inp); sys.exit(1)
    outp = sys.argv[2] if len(sys.argv)>=3 else os.path.splitext(inp)[0] + '.html'
    with open(inp, 'r', encoding='utf-8') as f: text = f.read()
    html_out = compile_htxt(text)
    with open(outp, 'w', encoding='utf-8') as f: f.write(html_out)
    print('Wrote', outp)

if __name__ == '__main__': main()
