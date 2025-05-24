import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Highlight from '@tiptap/extension-highlight'
import TextStyle from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import type { Editor } from '@tiptap/core'
import { forwardRef, useImperativeHandle, useEffect } from 'react'
import { Box, Paper, Typography, Divider, useTheme } from '@mui/material'
import './TipTapEditor.css'

interface TipTapEditorProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  label?: string
  fullWidth?: boolean
  fullHeight?: boolean
  minHeight?: string | number
  sx?: any // Allow for MUI sx prop
}

const TipTapEditor = forwardRef(({
  value,
  onChange,
  placeholder = 'Write requirements here...',
  label,
  fullWidth = true,
  fullHeight = false,
  minHeight = '200px',
  sx = {}
}: TipTapEditorProps, ref) => {
    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';
    
    const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3, 4, 5, 6]
        },
        codeBlock: {}
      }),
      Highlight,
      TextStyle,
      Color,
    ],
    content: value,
    editorProps: {
      attributes: {
        class: `tiptap-editor ${isDarkMode ? 'dark-theme' : 'light-theme'}`,
        style: `min-height: ${minHeight};`,
      },
    },
    onUpdate: ({ editor }) => {
      // Get the HTML content and pass it through onChange
      onChange(editor.getHTML())
    },
  })

  // Forward editor instance via imperative handle
  useImperativeHandle(ref, () => ({
    editor
  }))
  
  // Update editor content when value prop changes (for controlled component behavior)
  useEffect(() => {
    if (editor && editor.getHTML() !== value) {
      editor.commands.setContent(value)
    }
  }, [value, editor])
    // Create the toolbar for formatting options
  const MenuBar = ({ editor }: { editor: Editor | null }) => {
    const theme = useTheme();
    const isDarkMode = theme.palette.mode === 'dark';
    
    if (!editor) {
      return null
    }
  
    return (
      <div className={`tiptap-menu ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={editor.isActive('heading', { level: 1 }) ? 'is-active' : ''}
          title="Heading 1"
        >
          H1
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={editor.isActive('heading', { level: 2 }) ? 'is-active' : ''}
          title="Heading 2"
        >
          H2
        </button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
          className={editor.isActive('heading', { level: 3 }) ? 'is-active' : ''}
          title="Heading 3"
        >
          H3
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={editor.isActive('bold') ? 'is-active' : ''}
          title="Bold"
        >
          <strong>B</strong>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={editor.isActive('italic') ? 'is-active' : ''}
          title="Italic"
        >
          <em>I</em>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleStrike().run()}
          className={editor.isActive('strike') ? 'is-active' : ''}
          title="Strike"
        >
          <s>S</s>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive('bulletList') ? 'is-active' : ''}
          title="Bullet List"
        >
          • List
        </button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={editor.isActive('orderedList') ? 'is-active' : ''}
          title="Numbered List"
        >
          1. List
        </button>
        <button
          onClick={() => editor.chain().focus().toggleCodeBlock().run()}
          className={editor.isActive('codeBlock') ? 'is-active' : ''}
          title="Code Block"
        >
          {`<code/>`}
        </button>
        <button
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          className={editor.isActive('blockquote') ? 'is-active' : ''}
          title="Quote"
        >
          " Quote
        </button>
        <button
          onClick={() => editor.chain().focus().setHorizontalRule().run()}
          title="Horizontal Line"
        >
          ―
        </button>
        <button onClick={() => editor.chain().focus().undo().run()} title="Undo">
          ↩ Undo
        </button>
        <button onClick={() => editor.chain().focus().redo().run()} title="Redo">
          ↪ Redo
        </button>
      </div>
    )
  }
  
  return (
    <Box sx={{ width: fullWidth ? '100%' : 'auto', height: fullHeight ? '100%' : 'auto', ...(sx || {}) }}>
      {label && (
        <Typography variant="subtitle1" gutterBottom>
          {label}
        </Typography>
      )}
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 1, 
          minHeight, 
          height: fullHeight ? '100%' : 'auto',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: '8px',
          overflow: 'hidden',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}
      >
        {editor && <MenuBar editor={editor} />}
        {/* Bỏ Divider ở đây */}
        <Box 
          sx={{ 
            flexGrow: 1, 
            overflow: 'auto',
            borderRadius: '4px'
          }}
        >
          <EditorContent editor={editor} placeholder={placeholder} />
        </Box>
      </Paper>
    </Box>
  )
})

TipTapEditor.displayName = 'TipTapEditor'

export default TipTapEditor
