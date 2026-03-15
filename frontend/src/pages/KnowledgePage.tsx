import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  Card,
  Button,
  Input,
  Table,
  Tag,
  Space,
  Modal,
  Form,
  Select,
  message,
  Popconfirm,
  Typography,
  Tooltip,
  Empty,
  Spin,
  Tabs,
  Descriptions,
  List,
  Divider,
  Alert
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  BookOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  ExperimentOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import MarkdownEditor, { ChunkPreview } from '../components/MarkdownEditor'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs
const { Search } = Input

// 知识库文档类型
interface KnowledgeDoc {
  id: string
  title: string
  content?: string
  category: string
  source_type: 'knowledge' | 'resume'
  is_auto_generated: boolean
  chunk_count?: number
  structure?: {
    sections: Array<{ title: string; index: number }>
    total_chunks: number
  }
  created_at: string
  updated_at: string
}

// 搜索结果类型
interface SearchResult {
  content: string
  doc_id: string
  doc_title: string
  category: string
  header_path?: string
  section?: string
  score: number
}

// 分类选项
const CATEGORY_OPTIONS = [
  { value: 'general', label: '通用', color: 'default' },
  { value: 'ai', label: 'AI', color: 'purple' },
  { value: 'community', label: '社区', color: 'green' },
  { value: 'voice_room', label: '语音房', color: 'blue' }
]

const KnowledgePage: React.FC = () => {
  // 状态管理
  const [docs, setDocs] = useState<KnowledgeDoc[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterCategory, setFilterCategory] = useState<string>()
  
  // 模态框状态
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [isDetailModalVisible, setIsDetailModalVisible] = useState(false)
  const [editingDoc, setEditingDoc] = useState<KnowledgeDoc | null>(null)
  const [viewingDoc, setViewingDoc] = useState<KnowledgeDoc | null>(null)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  
  // Markdown编辑器状态
  const [editorContent, setEditorContent] = useState('')
  const [chunkPreviews, setChunkPreviews] = useState<ChunkPreview[]>([])
  const [previewLoading, setPreviewLoading] = useState(false)
  const previewTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // 搜索测试状态
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchLoading, setSearchLoading] = useState(false)

  // 获取文档列表
  const fetchDocs = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', currentPage.toString())
      params.append('page_size', pageSize.toString())
      if (searchKeyword) params.append('keyword', searchKeyword)
      if (filterCategory) params.append('category', filterCategory)

      const response = await fetch(`/api/v1/knowledge/docs?${params}`)
      if (response.ok) {
        const data = await response.json()
        setDocs(data.items || [])
        setTotal(data.total || 0)
      } else {
        message.error('获取知识库列表失败')
      }
    } catch (error) {
      console.error('获取知识库列表失败:', error)
      message.error('获取知识库列表失败')
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, searchKeyword, filterCategory])

  // 初始加载
  useEffect(() => {
    fetchDocs()
  }, [fetchDocs])

  // 清理定时器
  useEffect(() => {
    return () => {
      if (previewTimeoutRef.current) {
        clearTimeout(previewTimeoutRef.current)
      }
    }
  }, [])

  // 预览分块
  const previewChunks = useCallback(async (content: string) => {
    if (!content || content.length < 50) {
      setChunkPreviews([])
      return
    }
    
    setPreviewLoading(true)
    try {
      const response = await fetch('/api/v1/knowledge/preview-chunks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
      })
      
      if (response.ok) {
        const data = await response.json()
        setChunkPreviews(data.chunks || [])
      }
    } catch (error) {
      console.error('预览分块失败:', error)
    } finally {
      setPreviewLoading(false)
    }
  }, [])

  // 处理内容变化（带防抖）
  const handleContentChange = useCallback((content: string) => {
    setEditorContent(content)
    form.setFieldsValue({ content })
    
    // 清除之前的定时器
    if (previewTimeoutRef.current) {
      clearTimeout(previewTimeoutRef.current)
    }
    
    // 设置新的定时器，延迟800ms后预览
    previewTimeoutRef.current = setTimeout(() => {
      previewChunks(content)
    }, 800)
  }, [form, previewChunks])

  // 打开创建模态框
  const handleCreate = () => {
    setEditingDoc(null)
    setEditorContent('')
    setChunkPreviews([])
    form.resetFields()
    form.setFieldsValue({
      category: 'general',
      source_type: 'knowledge',
      content: ''
    })
    setIsModalVisible(true)
  }

  // 打开编辑模态框
  const handleEdit = async (doc: KnowledgeDoc) => {
    try {
      // 获取完整文档详情（包含 content）
      const response = await fetch(`/api/v1/knowledge/docs/${doc.id}`)
      if (!response.ok) {
        message.error('获取文档详情失败')
        return
      }
      
      const fullDoc = await response.json()
      setEditingDoc(fullDoc)
      const content = fullDoc.content || ''
      setEditorContent(content)
      form.setFieldsValue({
        title: fullDoc.title,
        content: content,
        category: fullDoc.category,
        source_type: fullDoc.source_type
      })
      // 立即预览
      previewChunks(content)
      setIsModalVisible(true)
    } catch (error) {
      message.error('获取文档详情失败')
    }
  }

  // 查看详情
  const handleViewDetail = async (doc: KnowledgeDoc) => {
    try {
      const response = await fetch(`/api/v1/knowledge/docs/${doc.id}`)
      if (response.ok) {
        const data = await response.json()
        setViewingDoc(data)
        setSearchResults([])
        setIsDetailModalVisible(true)
      } else {
        message.error('获取文档详情失败')
      }
    } catch (error) {
      message.error('获取文档详情失败')
    }
  }

  // 删除文档
  const handleDelete = async (id: string) => {
    try {
      const response = await fetch(`/api/v1/knowledge/docs/${id}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        message.success('删除成功')
        fetchDocs()
      } else {
        message.error('删除失败')
      }
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)

      const url = editingDoc 
        ? `/api/v1/knowledge/docs/${editingDoc.id}`
        : '/api/v1/knowledge/docs'
      
      const method = editingDoc ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      })

      if (response.ok) {
        message.success(editingDoc ? '更新成功' : '创建成功')
        setIsModalVisible(false)
        fetchDocs()
      } else {
        const error = await response.json()
        message.error(error.detail || '操作失败')
      }
    } catch (error) {
      console.error('提交失败:', error)
    } finally {
      setSubmitting(false)
    }
  }

  // 测试搜索
  const handleSearchTest = async (query: string) => {
    if (!query.trim() || !viewingDoc) return
    
    setSearchLoading(true)
    try {
      const response = await fetch('/api/v1/knowledge/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          doc_id: viewingDoc.id,
          top_k: 5
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.results || [])
      } else {
        message.error('搜索失败')
      }
    } catch (error) {
      message.error('搜索失败')
    } finally {
      setSearchLoading(false)
    }
  }

  // 获取分类标签颜色
  const getCategoryColor = (category: string) => {
    return CATEGORY_OPTIONS.find(c => c.value === category)?.color || 'default'
  }

  // 表格列定义
  const columns: ColumnsType<KnowledgeDoc> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <Space>
          <BookOutlined style={{ color: '#1890ff' }} />
          <Text strong>{text}</Text>
          {record.is_auto_generated && (
            <Tag color="orange" size="small">自动生成</Tag>
          )}
        </Space>
      )
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (category) => (
        <Tag color={getCategoryColor(category)}>
          {CATEGORY_OPTIONS.find(c => c.value === category)?.label || category}
        </Tag>
      )
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 80,
      align: 'center',
      render: (count) => count || '-'
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-CN')
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="text" 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个知识库文档吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="删除">
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={4} style={{ marginBottom: 8 }}>
            <BookOutlined style={{ marginRight: 8 }} />
            知识库管理
          </Title>
          <Text type="secondary">
            管理面试知识库，支持 Markdown 格式，系统会自动分块并建立向量索引
          </Text>
        </div>

        {/* 搜索和筛选 */}
        <Space wrap style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索标题"
            prefix={<SearchOutlined />}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            onPressEnter={fetchDocs}
            style={{ width: 250 }}
            allowClear
          />
          <Select
            placeholder="选择分类"
            value={filterCategory}
            onChange={setFilterCategory}
            style={{ width: 150 }}
            allowClear
          >
            {CATEGORY_OPTIONS.map(opt => (
              <Option key={opt.value} value={opt.value}>{opt.label}</Option>
            ))}
          </Select>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建文档
          </Button>
        </Space>

        {/* 文档列表 */}
        <Table
          columns={columns}
          dataSource={docs}
          rowKey="id"
          loading={loading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            onChange: (page, size) => {
              setCurrentPage(page)
              setPageSize(size || 10)
            },
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`
          }}
        />
      </Card>

      {/* 创建/编辑模态框 */}
      <Modal
        title={editingDoc ? '编辑知识库文档' : '新建知识库文档'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={() => setIsModalVisible(false)}
        width={1200}
        confirmLoading={submitting}
        okText="保存"
        cancelText="取消"
        bodyStyle={{ maxHeight: '70vh', overflow: 'auto' }}
      >
        <Form
          form={form}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="请输入文档标题" maxLength={100} showCount />
          </Form.Item>

          <Space style={{ width: '100%', marginBottom: 16 }}>
            <Form.Item
              name="category"
              label="分类"
              style={{ width: 200, marginBottom: 0 }}
              rules={[{ required: true, message: '请选择分类' }]}
            >
              <Select placeholder="选择分类">
                {CATEGORY_OPTIONS.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="source_type"
              label="来源类型"
              style={{ width: 200, marginBottom: 0 }}
            >
              <Select disabled>
                <Option value="knowledge">手动上传</Option>
                <Option value="resume">简历生成</Option>
              </Select>
            </Form.Item>
          </Space>

          <Form.Item
            name="content"
            label="内容"
            rules={[{ required: true, message: '请输入内容' }]}
            style={{ marginBottom: 0 }}
          >
            <MarkdownEditor
              value={editorContent}
              onChange={handleContentChange}
              chunkPreviews={chunkPreviews}
              loading={previewLoading}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="文档详情"
        open={isDetailModalVisible}
        onCancel={() => setIsDetailModalVisible(false)}
        width={900}
        footer={[
          <Button key="close" onClick={() => setIsDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {viewingDoc ? (
          <Tabs defaultActiveKey="content">
            <TabPane tab="内容" key="content">
              <div style={{ maxHeight: 500, overflow: 'auto' }}>
                <pre style={{ 
                  background: '#f6f8fa', 
                  padding: 16, 
                  borderRadius: 6,
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word'
                }}>
                  {viewingDoc.content}
                </pre>
              </div>
            </TabPane>
            <TabPane tab="文档结构" key="structure">
              {viewingDoc.structure ? (
                <div>
                  <Descriptions bordered column={1} size="small">
                    <Descriptions.Item label="总分块数">
                      {viewingDoc.structure.total_chunks}
                    </Descriptions.Item>
                  </Descriptions>
                  <Divider orientation="left">章节结构</Divider>
                  <List
                    dataSource={viewingDoc.structure.sections}
                    renderItem={(section, index) => (
                      <List.Item>
                        <Space>
                          <Tag color="blue">{index + 1}</Tag>
                          <Text>{section.title}</Text>
                        </Space>
                      </List.Item>
                    )}
                  />
                </div>
              ) : (
                <Empty description="暂无结构信息" />
              )}
            </TabPane>
            <TabPane 
              tab={
                <Space>
                  <ExperimentOutlined />
                  <span>搜索测试</span>
                </Space>
              } 
              key="search"
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Alert
                  message="混合检索测试（向量 + BM25 + RRF融合）"
                  description="输入搜索词测试混合检索效果。系统会同时使用向量语义检索和BM25关键词检索，通过RRF算法融合排序。"
                  type="info"
                  showIcon
                />
                
                <Search
                  placeholder="输入测试搜索词，例如：缓存穿透解决方案"
                  enterButton="搜索"
                  size="large"
                  loading={searchLoading}
                  onSearch={handleSearchTest}
                />
                
                {searchResults.length > 0 && (
                  <div>
                    <Divider orientation="left">
                      搜索结果（共 {searchResults.length} 条）
                    </Divider>
                    <List
                      dataSource={searchResults}
                      renderItem={(item: any, index) => (
                        <List.Item>
                          <div style={{ width: '100%' }}>
                            <div style={{ 
                              display: 'flex', 
                              justifyContent: 'space-between',
                              alignItems: 'center',
                              marginBottom: 8
                            }}>
                              <Space>
                                <Text strong style={{ fontSize: 14 }}>
                                  {index + 1}. {item.doc_title}
                                </Text>
                                {item.sources && item.sources.map((source: string) => (
                                  <Tag 
                                    key={source}
                                    color={source === 'vector' ? 'blue' : source === 'bm25' ? 'green' : 'default'}
                                    size="small"
                                  >
                                    {source === 'vector' ? '向量' : source === 'bm25' ? 'BM25' : source}
                                  </Tag>
                                ))}
                              </Space>
                              <Tag color="purple">
                                RRF: {item.score.toFixed(4)}
                              </Tag>
                            </div>
                            
                            {/* 显示详细来源信息 */}
                            {(item.vector_score !== undefined || item.bm25_score !== undefined) && (
                              <div style={{ 
                                fontSize: 11, 
                                color: '#666',
                                marginBottom: 8
                              }}>
                                {item.vector_rank && (
                                  <span style={{ marginRight: 16 }}>
                                    向量: 排名#{item.vector_rank} (分数: {item.vector_score.toFixed(3)})
                                  </span>
                                )}
                                {item.bm25_rank && (
                                  <span>
                                    BM25: 排名#{item.bm25_rank} (分数: {item.bm25_score.toFixed(3)})
                                  </span>
                                )}
                              </div>
                            )}
                            
                            {(item.header_path || item.section) && (
                              <div style={{ 
                                fontSize: 12, 
                                color: '#666',
                                marginBottom: 8
                              }}>
                                路径: {item.header_path || item.section}
                              </div>
                            )}
                            <div style={{ 
                              padding: 12,
                              background: '#f6f8fa',
                              borderRadius: 6,
                              fontSize: 13,
                              lineHeight: 1.6,
                              color: '#333'
                            }}>
                              {item.content.length > 300 
                                ? item.content.substring(0, 300) + '...' 
                                : item.content}
                            </div>
                          </div>
                        </List.Item>
                      )}
                    />
                  </div>
                )}
                
                {searchResults.length === 0 && !searchLoading && (
                  <Empty description="输入搜索词开始测试" />
                )}
              </Space>
            </TabPane>
            <TabPane tab="元数据" key="metadata">
              <Descriptions bordered column={1}>
                <Descriptions.Item label="ID">{viewingDoc.id}</Descriptions.Item>
                <Descriptions.Item label="标题">{viewingDoc.title}</Descriptions.Item>
                <Descriptions.Item label="分类">
                  <Tag color={getCategoryColor(viewingDoc.category)}>
                    {CATEGORY_OPTIONS.find(c => c.value === viewingDoc.category)?.label}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="来源">
                  {viewingDoc.source_type === 'knowledge' ? '手动上传' : '简历生成'}
                </Descriptions.Item>
                <Descriptions.Item label="分块数">
                  {viewingDoc.chunk_count || 0}
                </Descriptions.Item>
                <Descriptions.Item label="索引状态">
                  <Space>
                    <Tag color="blue">向量索引</Tag>
                    <Tag color="green">BM25索引</Tag>
                    <Tag color="purple">RRF融合</Tag>
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  {new Date(viewingDoc.created_at).toLocaleString('zh-CN')}
                </Descriptions.Item>
                <Descriptions.Item label="更新时间">
                  {new Date(viewingDoc.updated_at).toLocaleString('zh-CN')}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
          </Tabs>
        ) : (
          <Spin />
        )}
      </Modal>
    </div>
  )
}

export default KnowledgePage
