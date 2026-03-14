import React, { useState, useEffect, useCallback } from 'react'
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
  Badge,
  Empty,
  Spin,
  Tabs,
  Descriptions,
  List,
  Divider
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  BookOutlined,
  FileTextOutlined,
  TagsOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select
const { TabPane } = Tabs

// 知识库文档类型
interface KnowledgeDoc {
  id: string
  title: string
  content?: string
  category: string
  knowledge_type: 'technical' | 'behavioral' | 'career' | 'general'
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

// 分类选项
const CATEGORY_OPTIONS = [
  { value: 'backend', label: '后端开发', color: 'blue' },
  { value: 'frontend', label: '前端开发', color: 'green' },
  { value: 'ai', label: '人工智能', color: 'purple' },
  { value: 'devops', label: '运维/DevOps', color: 'orange' },
  { value: 'database', label: '数据库', color: 'cyan' },
  { value: 'architecture', label: '架构设计', color: 'red' },
  { value: 'soft_skill', label: '软技能', color: 'magenta' },
  { value: 'general', label: '通用', color: 'default' }
]

// 知识类型选项
const KNOWLEDGE_TYPE_OPTIONS = [
  { value: 'technical', label: '技术知识', color: 'processing' },
  { value: 'behavioral', label: '行为面试', color: 'warning' },
  { value: 'career', label: '职业规划', color: 'success' },
  { value: 'general', label: '通用', color: 'default' }
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
  const [filterType, setFilterType] = useState<string>()
  
  // 模态框状态
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [isDetailModalVisible, setIsDetailModalVisible] = useState(false)
  const [editingDoc, setEditingDoc] = useState<KnowledgeDoc | null>(null)
  const [viewingDoc, setViewingDoc] = useState<KnowledgeDoc | null>(null)
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  // 获取文档列表
  const fetchDocs = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', currentPage.toString())
      params.append('page_size', pageSize.toString())
      if (searchKeyword) params.append('keyword', searchKeyword)
      if (filterCategory) params.append('category', filterCategory)
      if (filterType) params.append('knowledge_type', filterType)

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
  }, [currentPage, pageSize, searchKeyword, filterCategory, filterType])

  // 初始加载
  useEffect(() => {
    fetchDocs()
  }, [fetchDocs])

  // 打开创建模态框
  const handleCreate = () => {
    setEditingDoc(null)
    form.resetFields()
    form.setFieldsValue({
      category: 'general',
      knowledge_type: 'technical',
      source_type: 'knowledge'
    })
    setIsModalVisible(true)
  }

  // 打开编辑模态框
  const handleEdit = (doc: KnowledgeDoc) => {
    setEditingDoc(doc)
    form.setFieldsValue({
      title: doc.title,
      content: doc.content,
      category: doc.category,
      knowledge_type: doc.knowledge_type,
      source_type: doc.source_type
    })
    setIsModalVisible(true)
  }

  // 查看详情
  const handleViewDetail = async (doc: KnowledgeDoc) => {
    try {
      const response = await fetch(`/api/v1/knowledge/docs/${doc.id}`)
      if (response.ok) {
        const data = await response.json()
        setViewingDoc(data)
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

  // 获取分类标签颜色
  const getCategoryColor = (category: string) => {
    return CATEGORY_OPTIONS.find(c => c.value === category)?.color || 'default'
  }

  // 获取知识类型标签
  const getKnowledgeTypeLabel = (type: string) => {
    return KNOWLEDGE_TYPE_OPTIONS.find(t => t.value === type)?.label || type
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
      title: '类型',
      dataIndex: 'knowledge_type',
      key: 'knowledge_type',
      width: 100,
      render: (type) => (
        <Badge 
          status={type === 'technical' ? 'processing' : type === 'behavioral' ? 'warning' : 'default'}
          text={getKnowledgeTypeLabel(type)}
        />
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
          <Select
            placeholder="选择类型"
            value={filterType}
            onChange={setFilterType}
            style={{ width: 150 }}
            allowClear
          >
            {KNOWLEDGE_TYPE_OPTIONS.map(opt => (
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
        width={900}
        confirmLoading={submitting}
        okText="保存"
        cancelText="取消"
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

          <Space style={{ width: '100%' }}>
            <Form.Item
              name="category"
              label="分类"
              style={{ width: 200 }}
              rules={[{ required: true, message: '请选择分类' }]}
            >
              <Select placeholder="选择分类">
                {CATEGORY_OPTIONS.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="knowledge_type"
              label="知识类型"
              style={{ width: 200 }}
              rules={[{ required: true, message: '请选择类型' }]}
            >
              <Select placeholder="选择类型">
                {KNOWLEDGE_TYPE_OPTIONS.map(opt => (
                  <Option key={opt.value} value={opt.value}>{opt.label}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="source_type"
              label="来源类型"
              style={{ width: 200 }}
            >
              <Select disabled>
                <Option value="knowledge">手动上传</Option>
                <Option value="resume">简历生成</Option>
              </Select>
            </Form.Item>
          </Space>

          <Form.Item
            name="content"
            label={
              <Space>
                <span>内容</span>
                <Tooltip title="支持 Markdown 格式，建议使用 ## 二级标题组织内容">
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                </Tooltip>
              </Space>
            }
            rules={[{ required: true, message: '请输入内容' }]}
          >
            <TextArea
              placeholder={`请输入 Markdown 格式内容

示例结构：
## 主题一
内容...

## 主题二
内容...
`}
              rows={16}
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="文档详情"
        open={isDetailModalVisible}
        onCancel={() => setIsDetailModalVisible(false)}
        width={800}
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
            <TabPane tab="元数据" key="metadata">
              <Descriptions bordered column={1}>
                <Descriptions.Item label="ID">{viewingDoc.id}</Descriptions.Item>
                <Descriptions.Item label="标题">{viewingDoc.title}</Descriptions.Item>
                <Descriptions.Item label="分类">
                  <Tag color={getCategoryColor(viewingDoc.category)}>
                    {CATEGORY_OPTIONS.find(c => c.value === viewingDoc.category)?.label}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="知识类型">
                  {getKnowledgeTypeLabel(viewingDoc.knowledge_type)}
                </Descriptions.Item>
                <Descriptions.Item label="来源">
                  {viewingDoc.source_type === 'knowledge' ? '手动上传' : '简历生成'}
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
