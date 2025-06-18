export interface Model {
  id: number;
  name: string;
  provider: string;
  base_url?: string;
  is_deleted: boolean;
}

export interface ModelCreate {
  name: string;
  provider: string;
  api_key: string;
  base_url?: string;
} 