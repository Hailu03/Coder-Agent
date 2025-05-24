import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';
import styled from '@emotion/styled';

interface TaskHistoryItem {
  task_id: string;
  status: string;
  requirements: string;
  language: string;
  created_at: string;
}

// adjust background color for light and dark mode
const HistoryContainer = styled.div`
    padding: 0;
    max-height: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-shadow: none;
`;


const HistoryList = styled.ul`
  list-style-type: none;
  padding: 8px 0;
  margin: 0;
  flex: 1;
  overflow-y: auto;
`;

const HistoryItem = styled.li`
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background-color:rgb(174, 174, 174);
  }

  &:last-child {
    border-bottom: none;
  }
`;

const TaskTitle = styled.div`
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  /* Xóa flex và justify-content để title sát trái */
`;

const TaskContent = styled.div`
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  /* Đảm bảo không có align center */
`;

const TaskMeta = styled.div`
  display: flex;
  align-items: center;
  font-size: 12px;
  margin-top: 4px;
  gap: 0;
`;

const Badge = styled.span<{ status: string }>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  flex-shrink: 0;
  margin-left: 8px;
  background-color: ${props => 
    props.status === 'COMPLETED' ? '#e6f7ed' : 
    props.status === 'FAILED' ? '#fde8e8' : 
    props.status === 'PROCESSING' ? '#e6f3ff' : '#f0f0f0'
  };
  color: ${props => 
    props.status === 'COMPLETED' ? '#0d653f' : 
    props.status === 'FAILED' ? '#b91c1c' : 
    props.status === 'PROCESSING' ? '#1a56db' : '#666666'
  };
  height: 20px;
`;

const LoadingState = styled.div`
  padding: 24px 0;
  text-align: center;
  color: #666;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const ErrorState = styled.div`
  padding: 24px 16px;
  text-align: center;
  color: #e53e3e;
  background-color: #fff5f5;
  margin: 16px;
  border-radius: 8px;
`;

const SolveHistory: React.FC = () => {  const [history, setHistory] = useState<TaskHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const data = await apiService.getHistory();
        setHistory(data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Unable to load history');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const handleSelectTask = (taskId: string) => {
    navigate(`/result/${taskId}`);
  };

  const extractTitle = (html: string): string => {
    // Ưu tiên lấy trong <h1>, <h2>, <h3>
    const headingMatch = html.match(/<h[1-3][^>]*>(.*?)<\/h[1-3]>/i);
    if (headingMatch) {
        // Loại bỏ thẻ HTML lồng bên trong (ví dụ <strong>)
        return headingMatch[1].replace(/<[^>]+>/g, '').trim();
    }
    // Nếu không có heading, lấy <strong> đầu tiên
    const strongMatch = html.match(/<strong[^>]*>(.*?)<\/strong>/i);
    if (strongMatch) {
        return strongMatch[1].replace(/<[^>]+>/g, '').trim();
    }
    // Nếu không có, lấy 30 ký tự đầu (loại bỏ thẻ)
    return html.replace(/<[^>]+>/g, '').trim().slice(0, 30);
    }

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return 'Invalid date';
    }
  };
  return (
    <HistoryContainer>
      {loading ? (
        <LoadingState>Loading...</LoadingState>
      ) : error ? (
        <ErrorState>Error: {error}</ErrorState>
      ) : (
        <HistoryList>
          {history.length === 0 ? (
            <LoadingState>No solution history available.</LoadingState>
          ) : (
            history.map((task) => (              
            
            <HistoryItem 
                key={task.task_id} 
                onClick={() => handleSelectTask(task.task_id)}
                >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    {/* Bên trái: title + language */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                    <TaskTitle style={{ marginBottom: 2 }}>
                        {task.requirements && extractTitle(task.requirements)}
                    </TaskTitle>
                    <span style={{ fontSize: 12, color: '#ccc' }}>{task.language}</span>
                    </div>
                    {/* Bên phải: status + date */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                    <Badge status={task.status}>{task.status}</Badge>
                    <span style={{ fontSize: 12, color: '#bbb', marginTop: 2 }}>
                        {task.created_at && formatDate(task.created_at)}
                    </span>
                    </div>
                </div>
            </HistoryItem>
            ))
          )}
        </HistoryList>
      )}
    </HistoryContainer>
  );
};

export default SolveHistory;
