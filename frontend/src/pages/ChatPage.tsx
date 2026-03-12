import React, { useState, useRef, useEffect } from 'react'
import { Card, Input, Button, Space, Typography, Spin, Collapse, Tag } from 'antd'
import { SendOutlined, UserOutlined, RobotOutlined, LoadingOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const { TextArea } = Input
const { Title, Text } = Typography
const { Panel } = Collapse

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: ThinkingStep[]
  timestamp: Date
}

interface ThinkingStep {
  step: string
  status: string
  detail: string
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [thinkingProcess, setThinkingProcess] = useState<ThinkingStep[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 发送消息
  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setThinkingProcess([])

    try {
      // 调用后端API（非流式版本用于测试）
      const response = await fetch('http://localhost:8000/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage.content,
          resume_data: {
            name: '张三',
            education: [{ school: '北京大学', major: '计算机科学' }],
            experience: [{ company: '字节跳动', position: '后端开发实习生' }]
          },
          job_info: {
            company: '腾讯',
            position: 'Java后端开发',
            level: 'P6'
          },
          history: messages.map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      })

      if (!response.ok) {
        throw new Error('请求失败')
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        thinking: data.thinking_process,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      setThinkingProcess(data.thinking_process || [])
    } catch (error) {
      console.error('发送消息失败:', error)
      // 添加错误消息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，服务暂时不可用，请稍后重试。',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // 处理回车键
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      {/* 聊天标题 */}
      <Card style={{ marginBottom: '16px' }}>
        <Space>
          <Title level={4} style={{ margin: 0 }}>面试模拟</Title>
          <Tag color="blue">腾讯 · Java后端开发</Tag>
        </Space>
      </Card>

      {/* 消息列表 */}
      <Card style={{ flex: 1, overflow: 'auto', marginBottom: '16px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.length === 0 && (
            <div style={{ textAlign: 'center', color: '#999', padding: '40px' }}>
              <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <p>开始面试吧！输入面试问题，Agent会以求职者身份回答。</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-start' : 'flex-end',
                gap: '12px'
              }}
            >
              {message.role === 'user' && (
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#1890ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserOutlined style={{ color: '#fff', fontSize: '20px' }} />
                </div>
              )}

              <div style={{ maxWidth: '70%' }}>
                <div style={{ marginBottom: '4px', fontSize: '12px', color: '#999' }}>
                  {message.role === 'user' ? '面试官（我）' : 'Agent（面试者）'}
                  {' '}
                  {message.timestamp.toLocaleTimeString()}
                </div>

                <div
                  style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    background: message.role === 'user' ? '#f0f0f0' : '#e6f7ff',
                    border: message.role === 'user' ? '1px solid #d9d9d9' : '1px solid #91d5ff'
                  }}
                >
                  {message.role === 'assistant' && message.thinking && message.thinking.length > 0 && (
                    <Collapse ghost style={{ marginBottom: '8px' }}>
                      <Panel
                        header={<Text type="secondary">思考过程 ({message.thinking.length} 步)</Text>}
                        key="thinking"
                      >
                        {message.thinking.map((step, index) => (
                          <div key={index} style={{ marginBottom: '8px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                            <Text strong>{step.step}</Text>
                            <div style={{ fontSize: '12px', color: '#666' }}>{step.detail}</div>
                          </div>
                        ))}
                      </Panel>
                    </Collapse>
                  )}

                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              </div>

              {message.role === 'assistant' && (
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#52c41a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <RobotOutlined style={{ color: '#fff', fontSize: '20px' }} />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <div style={{ maxWidth: '70%' }}>
                <div style={{ marginBottom: '4px', fontSize: '12px', color: '#999' }}>
                  Agent（面试者）正在思考...
                </div>
                <div style={{ padding: '12px 16px', borderRadius: '8px', background: '#e6f7ff', border: '1px solid #91d5ff' }}>
                  <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
                  {thinkingProcess.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      {thinkingProcess.map((step, index) => (
                        <div key={index} style={{ fontSize: '12px', color: '#666' }}>
                          {step.step}: {step.status === 'completed' ? '✓' : '⏳'} {step.detail}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#52c41a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <RobotOutlined style={{ color: '#fff', fontSize: '20px' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </Card>

      {/* 输入框 */}
      <Card>
        <Space style={{ width: '100%' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入面试问题..."
            autoSize={{ minRows: 2, maxRows: 4 }}
            style={{ width: 'calc(100vw - 500px)' }}
            disabled={isLoading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={isLoading}
            disabled={!inputValue.trim()}
            size="large"
          >
            发送
          </Button>
        </Space>
      </Card>
    </div>
  )
}

export default ChatPage
