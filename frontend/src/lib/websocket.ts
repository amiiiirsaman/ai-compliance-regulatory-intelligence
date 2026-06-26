import { useEffect, useRef, useCallback } from 'react'
import { useDispatch } from 'react-redux'
import { 
  updateReviewFromWebSocket, 
  addBedrockCall, 
  resetAgentProgress, 
  updateAgentStatus,
  fetchReview,
  fetchBedrockCalls
} from '@/store/slices/reviewsSlice'
import { AppDispatch } from '@/store'

interface WebSocketMessage {
  type: string
  review_id?: string
  data?: any
  timestamp?: string
}

export function useReviewWebSocket(reviewId: string | undefined) {
  const wsRef = useRef<WebSocket | null>(null)
  const dispatch = useDispatch<AppDispatch>()
  
  const connect = useCallback(() => {
    if (!reviewId) return
    
    const token = localStorage.getItem('token')
    if (!token) return
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/reviews/${reviewId}?token=${token}`
    
    const ws = new WebSocket(wsUrl)
    
    ws.onopen = () => {
      console.log('WebSocket connected for review:', reviewId)
      // Reset agent progress when connection opens
      dispatch(resetAgentProgress())
    }
    
    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)
        console.log('WebSocket message:', message.type, message.data)
        
        switch (message.type) {
          case 'connected':
            // Initial connection confirmation
            break
            
          case 'review_started':
            dispatch(resetAgentProgress())
            dispatch(updateReviewFromWebSocket({
              review_id: message.review_id,
              status: 'in_progress',
              ...message.data,
            }))
            break
            
          case 'review_completed':
            dispatch(updateReviewFromWebSocket({
              review_id: message.review_id,
              status: 'complete',
              ...message.data,
            }))
            // IMPORTANT: Refetch full review data to get violations, corrections, scores
            if (reviewId) {
              setTimeout(() => {
                dispatch(fetchReview(reviewId))
                dispatch(fetchBedrockCalls(reviewId))
              }, 500) // Small delay to ensure DB is updated
            }
            break
            
          case 'review_failed':
            dispatch(updateReviewFromWebSocket({
              review_id: message.review_id,
              status: 'failed',
              ...message.data,
            }))
            break
            
          case 'agent_started':
            if (message.data?.agent_name) {
              dispatch(updateAgentStatus({
                agentName: message.data.agent_name,
                status: 'running',
                startTime: message.timestamp || new Date().toISOString(),
              }))
            }
            break
            
          case 'agent_completed':
            if (message.data?.agent_name) {
              dispatch(updateAgentStatus({
                agentName: message.data.agent_name,
                status: 'completed',
                endTime: message.timestamp || new Date().toISOString(),
              }))
            }
            break
            
          case 'agent_failed':
            if (message.data?.agent_name) {
              dispatch(updateAgentStatus({
                agentName: message.data.agent_name,
                status: 'failed',
                endTime: message.timestamp || new Date().toISOString(),
                error: message.data.error,
              }))
            }
            break
            
          case 'bedrock_call':
            if (message.data) {
              dispatch(addBedrockCall(message.data))
              // DO NOT update agent status from bedrock_call - let agent_completed/agent_failed handle it
            }
            break
            
          case 'violation_found':
            // Real-time violation found - will be fetched on completion
            break
            
          case 'review_progress':
            dispatch(updateReviewFromWebSocket({
              review_id: message.review_id,
              ...message.data,
            }))
            break
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }
    
    ws.onclose = () => {
      console.log('WebSocket disconnected')
      // Attempt reconnect after delay
      setTimeout(() => {
        if (wsRef.current === ws) {
          connect()
        }
      }, 3000)
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    wsRef.current = ws
  }, [reviewId, dispatch])
  
  useEffect(() => {
    connect()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [connect])
  
  return wsRef.current
}
