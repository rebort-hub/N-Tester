import request from '/@/utils/request';

export const aiKnowledgeConfigApi = {
	getGlobal: () => request.get('/v1/ai/knowledge-config/global'),
	saveGlobal: (data: any) => request.put('/v1/ai/knowledge-config/global', data),
	testEmbedding: (data: any) => request.post('/v1/ai/knowledge-config/test-embedding', data),
	testVectorDb: (data: any) => request.post('/v1/ai/knowledge-config/test-vector-db', data),
};

