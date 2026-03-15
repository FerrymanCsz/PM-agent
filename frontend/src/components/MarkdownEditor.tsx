import React, { useState, useEffect, useCallback } from 'react'
import MDEditor from '@uiw/react-md-editor'
import { Card, Space, Tag, Typography, Alert, Spin } from 'antd'
import { FileTextOutlined, InfoCircleOutlined } from '@ant-design/icons'

const { Text } = Typography

export interface ChunkPreview {
  index: number
  title: string
  path: string
  size: number
  will_split: boolean
  preview: string
}

interface MarkdownEditorProps {
  value: string
  onChange: (value: string) => void
  chunkPreviews?: ChunkPreview[]
  loading?: boolean
}

const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  chunkPreviews,
  loading
}) => {
  const [isDarkMode, setIsDarkMode] = useState(false)

  // 检测系统主题
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setIsDarkMode(mediaQuery.matches)
    
    const handler = (e: MediaQueryListEvent) => setIsDarkMode(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  // 自定义工具栏命令
  const customCommands = [
    {
      name: 'bold',
      keyCommand: 'bold',
      button: { 'aria-label': 'Bold' },
      icon: <span style={{ fontWeight: 'bold' }}>B</span>,
      execute: (state: any, api: any) => {
        const modifyText = `**${state.selectedText || 'bold'}**`
        api.replaceSelection(modifyText)
      }
    },
    {
      name: 'italic',
      keyCommand: 'italic',
      button: { 'aria-label': 'Italic' },
      icon: <span style={{ fontStyle: 'italic' }}>I</span>,
      execute: (state: any, api: any) => {
        const modifyText = `*${state.selectedText || 'italic'}*`
        api.replaceSelection(modifyText)
      }
    },
    {
      name: 'header',
      keyCommand: 'header',
      button: { 'aria-label': 'Header' },
      icon: <span>H</span>,
      execute: (state: any, api: any) => {
        const modifyText = `## ${state.selectedText || 'Header'}\n`
        api.replaceSelection(modifyText)
      }
    },
    {
      name: 'code',
      keyCommand: 'code',
      button: { 'aria-label': 'Code' },
      icon: <span>{`</>`}</span>,
      execute: (state: any, api: any) => {
        const modifyText = `\`\`\`\n${state.selectedText || 'code'}\n\`\`\``
        api.replaceSelection(modifyText)
      }
    },
    {
      name: 'link',
      keyCommand: 'link',
      button: { 'aria-label': 'Link' },
      icon: <span>🔗</span>,
      execute: (state: any, api: any) => {
        const modifyText = `[${state.selectedText || 'link'}](url)`
        api.replaceSelection(modifyText)
      }
    },
    {
      name: 'quote',
      keyCommand: 'quote',
      button: { 'aria-label': 'Quote' },
      icon: <span>"</span>,
      execute: (state: any, api: any) => {
        const modifyText = `> ${state.selectedText || 'quote'}`
        api.replaceSelection(modifyText)
      }
    },
    {
      name: 'unordered-list',
      keyCommand: 'unordered-list',
      button: { 'aria-label': 'Unordered List' },
      icon: <span>•</span>,
      execute: (state: any, api: any) => {
        const modifyText = `- ${state.selectedText || 'item'}`
        api.replaceSelection(modifyText)
      }
    },
    {
      name: 'ordered-list',
      keyCommand: 'ordered-list',
      button: { 'aria-label': 'Ordered List' },
      icon: <span>1.</span>,
      execute: (state: any, api: any) => {
        const modifyText = `1. ${state.selectedText || 'item'}`
        api.replaceSelection(modifyText)
      }
    }
  ]

  return (
    <div style={{ display: 'flex', gap: 16, height: 600 }}>
      {/* 左侧编辑器 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div 
          data-color-mode={isDarkMode ? 'dark' : 'light'}
          style={{ 
            flex: 1,
            border: '1px solid #d9d9d9',
            borderRadius: 6,
            overflow: 'hidden'
          }}
        >
          <MDEditor
            value={value}
            onChange={(val) => onChange(val || '')}
            height={600}
            preview="edit"
            hideToolbar={false}
            toolbarHeight={40}
            commands={customCommands as any}
            textareaProps={{
              placeholder: '请输入 Markdown 格式内容...\n\n支持使用 ## 二级标题组织内容'
            }}
          />
        </div>
        <Text type="secondary" style={{ marginTop: 8, fontSize: 12 }}>
          <InfoCircleOutlined style={{ marginRight: 4 }} />
          提示：使用 ## 二级标题组织内容，系统会自动按标题分块建立索引
        </Text>
      </div>
      
      {/* 右侧分块预览 */}
      <Card 
        title={
          <Space>
            <FileTextOutlined />
            <span>分块预览</span>
            {chunkPreviews && chunkPreviews.length > 0 && (
              <Tag color="blue">{chunkPreviews.length} 个块</Tag>
            )}
          </Space>
        }
        style={{ width: 380, overflow: 'auto' }}
        bodyStyle={{ padding: 12, maxHeight: 540, overflow: 'auto' }}
        loading={loading}
      >
        {!chunkPreviews || chunkPreviews.length === 0 ? (
          <Alert
            message="输入内容后自动预览分块"
            description="系统会按二级标题(##)自动分割文档，每个章节独立索引。"
            type="info"
            showIcon
          />
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size="small">
            {chunkPreviews.map((chunk) => (
              <div 
                key={chunk.index}
                style={{ 
                  padding: 12,
                  background: chunk.will_split ? '#fff7e6' : '#f6ffed',
                  border: `1px solid ${chunk.will_split ? '#ffd591' : '#b7eb8f'}`,
                  borderRadius: 6,
                  marginBottom: 8
                }}
              >
                <Space style={{ marginBottom: 4 }}>
                  <Text strong>块 {chunk.index + 1}</Text>
                  <Tag 
                    color={chunk.will_split ? 'orange' : 'green'}
                    size="small"
                  >
                    {chunk.size} 字符
                    {chunk.will_split && ' (将分割)'}
                  </Tag>
                </Space>
                
                {chunk.path && (
                  <div style={{ 
                    fontSize: 11, 
                    color: '#666',
                    marginBottom: 4,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    路径: {chunk.path}
                  </div>
                )}
                
                <div style={{ 
                  fontSize: 12, 
                  color: '#333',
                  lineHeight: 1.5,
                  maxHeight: 80,
                  overflow: 'hidden',
                  display: '-webkit-box',
                  WebkitLineClamp: 4,
                  WebkitBoxOrient: 'vertical'
                }}>
                  {chunk.preview}
                </div>
              </div>
            ))}
            
            {chunkPreviews.some(c => c.will_split) && (
              <Alert
                message="部分块过大将被自动分割"
                description="超过1000字符的块会按句子进一步分割，保持语义完整。"
                type="warning"
                showIcon
                style={{ marginTop: 8 }}
              />
            )}
          </Space>
        )}
      </Card>
    </div>
  )
}

export default MarkdownEditor
