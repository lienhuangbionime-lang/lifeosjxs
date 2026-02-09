// 檔案: frontend-body/lib/types/api-schema.ts


export interface Project {
  id: string;
  created_at?: string;
  name: string;
  category?: 'macro' | 'micro' | 'daemon'; // [NEW]
  status: 'active' | 'archived' | 'completed' | 'idea';
  progress: number;
  meta: {
    vibe?: string;
    emoji?: string;
    cover_image?: string;
    [key: string]: any;
  };
  tags?: string[];
}

export interface paths {

  "/api/v1/ingest": {
    post: {
      requestBody: {
        content: {
          "application/json": {
            text: string;
            date: string;
          };
        };
      };
      responses: {
        200: {
          content: {
            "application/json": {
              markdown_body: string;
              meta: {
                metrics: {
                  mood: number;
                  focus: number;
                  energy: number;
                };
              };
            };
          };
        };
      };
    };
  };
  "/api/v1/memories/daily": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": Array<{
              date: string;
              structured_data: any;
            }>;
          };
        };
      };
    };
  };
  "/api/v1/system/evolve": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": {
              message: string;
              current_model?: string;
            };
          };
        };
      };
    };
  };
}
