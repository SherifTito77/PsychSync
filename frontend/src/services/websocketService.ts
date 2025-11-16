import { io, Socket } from 'socket.io-client';
export interface NotificationMessage {
  id: string;
  type: 'training_reminder' | 'compliance_alert' | 'feedback_update' | 'system';
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  timestamp: string;
  data?: any;
  read: boolean;
}
class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Function[]> = new Map();
  connect(token: string) {
    if (this.socket?.connected) {
      return;
    }
    this.socket = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
      auth: { token },
      transports: ['websocket', 'polling'],
    });
    this.setupEventListeners();
  }
  private setupEventListeners() {
    if (!this.socket) return;
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected');
    });
    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emit('disconnected', reason);
      if (reason === 'io server disconnect') {
        // Server disconnected, reconnect manually
        this.reconnect();
      }
    });
    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnect();
    });
    this.socket.on('notification', (notification: NotificationMessage) => {
      this.emit('notification', notification);
    });
    this.socket.on('compliance_update', (data) => {
      this.emit('compliance_update', data);
    });
    this.socket.on('training_update', (data) => {
      this.emit('training_update', data);
    });
    this.socket.on('feedback_update', (data) => {
      this.emit('feedback_update', data);
    });
  }
  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.socket?.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }
  // Event emitter methods
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }
  off(event: string, callback: Function) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }
  private emit(event: string, data?: any) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }
  // Send messages to server
  sendNotificationRead(notificationId: string) {
    this.socket?.emit('mark_notification_read', { notificationId });
  }
  subscribeToComplianceUpdates() {
    this.socket?.emit('subscribe_compliance');
  }
  subscribeToTrainingUpdates() {
    this.socket?.emit('subscribe_training');
  }
  subscribeToFeedbackUpdates() {
    this.socket?.emit('subscribe_feedback');
  }
  // Join specific rooms for targeted updates
  joinRoom(room: string) {
    this.socket?.emit('join_room', { room });
  }
  leaveRoom(room: string) {
    this.socket?.emit('leave_room', { room });
  }
}
export const websocketService = new WebSocketService();