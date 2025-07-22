import { BaseResponse } from './common';

// User related types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  is_active?: boolean;
}

export interface UserPasswordUpdate {
  current_password: string;
  new_password: string;
}

export interface UserResponse extends Omit<BaseResponse, 'message'> {
  data: User;
}

export interface UserListResponse extends BaseResponse {
  users: User[];
  total_count: number;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  superusers: number;
  users_created_today: number;
  users_created_this_week: number;
  users_created_this_month: number;
  last_updated: string;
}

export interface UserStatsResponse extends Omit<BaseResponse, 'message'> {
  data: UserStats;
}