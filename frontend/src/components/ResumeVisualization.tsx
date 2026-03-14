import React, { useState } from 'react'
import {
  Card,
  Tag,
  Timeline,
  Descriptions,
  Space,
  Typography,
  Avatar,
  Row,
  Col,
  Collapse,
  Button,
  Modal,
  Divider
} from 'antd'
import {
  UserOutlined,
  BookOutlined,
  CarryOutOutlined,
  ToolOutlined,
  ProjectOutlined,
  FileTextOutlined,
  EyeOutlined,
  MailOutlined,
  PhoneOutlined,
  EnvironmentOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

interface Education {
  school: string
  major: string
  degree?: string
  start_date?: string
  end_date?: string
}

interface WorkExperience {
  company: string
  position: string
  department?: string
  start_date?: string
  end_date?: string
  description?: string
}

interface Project {
  name: string
  description?: string
  technologies?: string[]
  role?: string
  achievements?: string[]
  start_date?: string
  end_date?: string
}

interface ResumeData {
  name?: string
  gender?: string
  age?: number
  phone?: string
  email?: string
  location?: string
  education?: Education[]
  experience?: WorkExperience[]
  skills?: string[]
  projects?: Project[]
  summary?: string
}

interface ResumeVisualizationProps {
  data: ResumeData
}

const ResumeVisualization: React.FC<ResumeVisualizationProps> = ({ data }) => {
  const [rawJsonVisible, setRawJsonVisible] = useState(false)

  // 基本信息卡片
  const renderBasicInfo = () => (
    <Card style={{ marginBottom: 16 }}>
      <Row gutter={16} align="middle">
        <Col>
          <Avatar size={80} icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
        </Col>
        <Col flex="auto">
          <Space direction="vertical" size="small">
            <Title level={3} style={{ margin: 0 }}>{data.name || '未知姓名'}</Title>
            <Space>
              {data.gender && <Tag>{data.gender}</Tag>}
              {data.age && <Tag>{data.age}岁</Tag>}
              {data.location && (
                <Tag icon={<EnvironmentOutlined />}>{data.location}</Tag>
              )}
            </Space>
            <Space>
              {data.phone && (
                <Text type="secondary">
                  <PhoneOutlined /> {data.phone}
                </Text>
              )}
              {data.email && (
                <Text type="secondary">
                  <MailOutlined /> {data.email}
                </Text>
              )}
            </Space>
          </Space>
        </Col>
      </Row>
      {data.summary && (
        <>
          <Divider />
          <Paragraph>
            <FileTextOutlined /> {data.summary}
          </Paragraph>
        </>
      )}
    </Card>
  )

  // 教育背景时间轴
  const renderEducation = () => {
    if (!data.education || data.education.length === 0) return null

    return (
      <Card
        title={<><BookOutlined /> 教育背景</>}
        style={{ marginBottom: 16 }}
      >
        <Timeline mode="left">
          {data.education.map((edu, index) => (
            <Timeline.Item key={index}>
              <Space direction="vertical" size="small">
                <Text strong>{edu.school}</Text>
                <Text>{edu.major} {edu.degree && `· ${edu.degree}`}</Text>
                {(edu.start_date || edu.end_date) && (
                  <Text type="secondary">
                    {edu.start_date || '未知'} - {edu.end_date || '至今'}
                  </Text>
                )}
              </Space>
            </Timeline.Item>
          ))}
        </Timeline>
      </Card>
    )
  }

  // 工作经历卡片
  const renderWorkExperience = () => {
    if (!data.experience || data.experience.length === 0) return null

    return (
      <Card
        title={<><CarryOutOutlined /> 工作经历</>}
        style={{ marginBottom: 16 }}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {data.experience.map((exp, index) => (
            <Card
              key={index}
              size="small"
              type="inner"
              title={
                <Space>
                  <Text strong>{exp.company}</Text>
                  <Tag color="blue">{exp.position}</Tag>
                  {exp.department && <Tag>{exp.department}</Tag>}
                </Space>
              }
              extra={
                (exp.start_date || exp.end_date) && (
                  <Text type="secondary">
                    {exp.start_date || '未知'} - {exp.end_date || '至今'}
                  </Text>
                )
              }
            >
              {exp.description && (
                <Paragraph>{exp.description}</Paragraph>
              )}
            </Card>
          ))}
        </Space>
      </Card>
    )
  }

  // 技能标签云
  const renderSkills = () => {
    if (!data.skills || data.skills.length === 0) return null

    return (
      <Card
        title={<><ToolOutlined /> 技能特长</>}
        style={{ marginBottom: 16 }}
      >
        <Space wrap>
          {data.skills.map((skill, index) => (
            <Tag key={index} color="green" style={{ fontSize: 14, padding: '4px 12px' }}>
              {skill}
            </Tag>
          ))}
        </Space>
      </Card>
    )
  }

  // 项目经历折叠面板
  const renderProjects = () => {
    if (!data.projects || data.projects.length === 0) return null

    return (
      <Card
        title={<><ProjectOutlined /> 项目经历</>}
        style={{ marginBottom: 16 }}
      >
        <Collapse>
          {data.projects.map((project, index) => (
            <Panel
              key={index}
              header={
                <Space>
                  <Text strong>{project.name}</Text>
                  {project.role && <Tag color="purple">{project.role}</Tag>}
                </Space>
              }
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {project.description && (
                  <Paragraph>{project.description}</Paragraph>
                )}
                {project.technologies && project.technologies.length > 0 && (
                  <div>
                    <Text type="secondary">技术栈：</Text>
                    <Space wrap>
                      {project.technologies.map((tech, idx) => (
                        <Tag key={idx} size="small">{tech}</Tag>
                      ))}
                    </Space>
                  </div>
                )}
                {project.achievements && project.achievements.length > 0 && (
                  <div>
                    <Text type="secondary">主要成果：</Text>
                    <ul>
                      {project.achievements.map((achievement, idx) => (
                        <li key={idx}>{achievement}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Space>
            </Panel>
          ))}
        </Collapse>
      </Card>
    )
  }

  return (
    <div>
      {renderBasicInfo()}
      {renderEducation()}
      {renderWorkExperience()}
      {renderSkills()}
      {renderProjects()}

      {/* 查看原始 JSON */}
      <Card>
        <Button
          type="dashed"
          icon={<EyeOutlined />}
          onClick={() => setRawJsonVisible(true)}
          block
        >
          查看原始 JSON 数据
        </Button>
      </Card>

      {/* 原始 JSON 弹窗 */}
      <Modal
        title="原始简历数据 (JSON)"
        open={rawJsonVisible}
        onCancel={() => setRawJsonVisible(false)}
        footer={null}
        width={800}
      >
        <pre
          style={{
            background: '#f6f8fa',
            padding: 16,
            borderRadius: 8,
            maxHeight: '60vh',
            overflow: 'auto',
            fontSize: 12
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      </Modal>
    </div>
  )
}

export default ResumeVisualization
