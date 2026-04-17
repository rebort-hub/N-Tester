﻿<<template>
	<div class="api-detail-container" :class="{'is-embedded': props.embedded}">
		<el-card class="api-detail-card">
			<!-- 顶部大 Tab（嵌入模式下隐藏）-->
			<el-tabs v-if="!props.embedded" v-model="mainTab" class="main-tabs">
				<el-tab-pane label="调试" name="debug" />
				<el-tab-pane label="接口文档" name="doc" />
				<el-tab-pane label="调试记录" name="history" />
				<el-tab-pane label="Mock" name="mock" />
			</el-tabs>

			<!-- 调试面板 -->
			<div v-show="mainTab==='debug'" class="api-detail-content">
				<!-- URL bar -->
				<div class="api-detail-header">
					<div class="req-url-bar">
						<el-select v-model="req.method" class="method-select" :style="{ '--method-color': currentMethodColor }">
							<el-option v-for="(m, i) in method_list" :key="i" :label="m.name" :value="m.value">
								<span :style="{ color: m.color, fontWeight: 600 }">{{ m.name }}</span>
							</el-option>
						</el-select>
						<el-input v-model="req.url" placeholder="请输入请求地址" clearable class="url-input" />
						<el-button type="primary" @click="sendRequest" class="send-btn">发送</el-button>
						<el-dropdown @command="handleSaveCommand">
							<el-button type="success" class="save-btn">保存项 <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
							<template #dropdown>
								<el-dropdown-menu>
									<el-dropdown-item command="save">直接保存</el-dropdown-item>
									<el-dropdown-item command="saveAsCase">保存测试用例</el-dropdown-item>
								</el-dropdown-menu>
							</template>
						</el-dropdown>
					</div>
				</div>

				<div class="api-detail-body">
					<!-- 请求区 -->
					<div class="request-section">
						<div class="panel-card">
							<el-tabs v-model="req_active" class="apifox-tabs" style="height: 100%">
								<!-- Params -->
								<el-tab-pane name="params">
									<template #label>
										<el-badge :show-zero="false" :value="req.params.length" :offset="[13, 2]" type="danger">Params</el-badge>
									</template>
									<div style="overflow: auto; height: 100%">
										<div v-for="(p, i) in req.params" :key="i" style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
											<el-checkbox v-model="p.status" />
											<el-input v-model="p.key" placeholder="参数名" style="flex:1" size="small" />
											<el-input v-model="p.value" placeholder="参数值" style="flex:1" size="small" />
											<el-button type="danger" link size="small" @click="removeParam(i)">删除</el-button>
										</div>
										<el-button type="primary" link size="small" @click="addParam">+ 添加参数</el-button>
									</div>
								</el-tab-pane>
								<!-- Header -->
								<el-tab-pane name="header">
									<template #label>
										<el-badge :show-zero="false" :value="req.header.length" :offset="[13, 2]" type="danger">Header</el-badge>
									</template>
									<div style="overflow: auto; height: 100%">
										<div v-for="(h, i) in req.header" :key="i" style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
											<el-checkbox v-model="h.status" />
											<el-input v-model="h.key" placeholder="Header名" style="flex:1" size="small" />
											<el-input v-model="h.value" placeholder="Header值" style="flex:1" size="small" />
											<el-button type="danger" link size="small" @click="removeHeader(i)">删除</el-button>
										</div>
										<el-button type="primary" link size="small" @click="addHeader">+ 添加Header</el-button>
									</div>
								</el-tab-pane>
								<!-- Body -->
								<el-tab-pane label="Body" name="body">
									<div class="body-pane">
										<div class="body-type-bar">
											<span v-for="bt in bodyTypes" :key="bt.value" class="body-type-item" :class="{ active: req.body_type === bt.value }" @click="req.body_type = bt.value">{{ bt.label }}</span>
											<!-- <div class="body-type-bar-right">
												<el-select v-model="req.params_id" clearable placeholder="非必选：参数依赖" size="small" style="width: 160px">
													<el-option v-for="(p, i) in params_list" :key="i" :label="p.name" :value="p.id" />
												</el-select>
											</div> -->
										</div>
										<div class="body-content">
											<div v-if="req.body_type === 1" class="body-empty">该请求没有 Body</div>
											<div v-else-if="req.body_type === 2" class="body-editor">
												<div class="code-editor-wrap" style="height:100%">
													<div class="code-editor-lang">JSON</div>
													<div class="json-editor-inner">
														<JsonEditor v-model:value="req.body" height="100%" />
													</div>
												</div>
											</div>
											<div v-else-if="req.body_type === 3" class="body-kv">
												<div class="kv-header"><span class="kv-col-check"></span><span class="kv-col-key">参数名</span><span class="kv-col-val">参数值</span><span class="kv-col-act"></span></div>
												<div v-for="(f, i) in req.form_data" :key="i" class="kv-row">
													<el-checkbox v-model="f.status" class="kv-col-check" />
													<el-input v-model="f.key" placeholder="参数名" class="kv-col-key" size="small" />
													<el-input v-model="f.value" placeholder="参数值" class="kv-col-val" size="small" />
													<el-button type="danger" link size="small" class="kv-col-act" @click="removeFormData(i)">删除</el-button>
												</div>
												<el-button type="primary" link size="small" style="margin-top:6px" @click="addFormData">+ 添加参数</el-button>
											</div>
											<div v-else-if="req.body_type === 4" class="body-kv">
												<div class="kv-header"><span class="kv-col-check"></span><span class="kv-col-key">参数名</span><span class="kv-col-val">参数值</span><span class="kv-col-act"></span></div>
												<div v-for="(f, i) in req.form_urlencoded" :key="i" class="kv-row">
													<el-checkbox v-model="f.status" class="kv-col-check" />
													<el-input v-model="f.key" placeholder="参数名" class="kv-col-key" size="small" />
													<el-input v-model="f.value" placeholder="参数值" class="kv-col-val" size="small" />
													<el-button type="danger" link size="small" class="kv-col-act" @click="removeFormUrlencoded(i)">删除</el-button>
												</div>
												<el-button type="primary" link size="small" style="margin-top:6px" @click="addFormUrlencoded">+ 添加参数</el-button>
											</div>
											<div v-else-if="req.body_type === 5" class="body-binary">
												<el-upload :show-file-list="false" :limit="1" :http-request="uploadBinaryFile">
													<el-button type="primary" plain size="small">选择文件并上传</el-button>
												</el-upload>
												<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px">
													<el-tag v-for="(file, i) in req.file_path" :key="file+i" type="success" closable @close="req.file_path.splice(i,1)">{{ file }}</el-tag>
												</div>
											</div>
											<div v-else-if="req.body_type === 6" class="body-editor">
												<div class="code-editor-wrap">
													<div class="code-editor-lang">XML</div>
													<textarea v-model="req.xml_body" class="code-textarea" placeholder="请输入 XML 内容" spellcheck="false"></textarea>
												</div>
											</div>
											<div v-else-if="req.body_type === 7" class="body-editor">
												<div class="code-editor-wrap">
													<div class="code-editor-lang">Text</div>
													<textarea v-model="req.text_body" class="code-textarea" placeholder="请输入纯文本内容" spellcheck="false"></textarea>
												</div>
											</div>
											<div v-else-if="req.body_type === 8" class="body-editor">
												<div class="code-editor-wrap" style="flex:1">
													<div class="code-editor-lang">GraphQL · Query</div>
													<textarea v-model="req.graphql_query" class="code-textarea" placeholder="请输入 GraphQL Query" spellcheck="false" style="flex:1"></textarea>
												</div>
												<div class="code-editor-wrap" style="margin-top:8px">
													<div class="code-editor-lang">Variables · JSON</div>
													<textarea v-model="req.graphql_variables" class="code-textarea" placeholder='{"key": "value"}' spellcheck="false" style="min-height:80px"></textarea>
												</div>
											</div>
										</div>
									</div>
								</el-tab-pane>
								<!-- Cookies -->
								<el-tab-pane name="cookies">
									<template #label>
										<el-badge :show-zero="false" :value="req.cookies ? req.cookies.length : 0" :offset="[13, 2]" type="danger">Cookies</el-badge>
									</template>
									<div style="overflow:auto;height:100%">
										<div v-for="(c, i) in (req.cookies || [])" :key="i" style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
											<el-checkbox v-model="c.status" />
											<el-input v-model="c.name" placeholder="Cookie 名称" style="width:30%" size="small" />
											<el-input v-model="c.value" placeholder="Cookie 值" style="width:40%" size="small" />
											<el-input v-model="c.domain" placeholder="Domain（可选）" style="width:20%" size="small" />
											<el-button type="danger" link size="small" @click="removeCookie(i)">删除</el-button>
										</div>
										<el-button type="primary" link size="small" style="margin-top:6px" @click="addCookie">+ 添加 Cookie</el-button>
									</div>
								</el-tab-pane>
								<!-- Auth -->
								<el-tab-pane name="auth">
									<template #label><span>Auth</span></template>
									<div style="padding:8px 0">
										<el-form label-width="120px">
											<el-form-item label="认证类型：">
												<el-select v-model="req.auth_type" style="width:220px" placeholder="请选择认证类型">
													<el-option label="无认证" value="none" />
													<el-option label="Bearer Token" value="bearer" />
													<el-option label="Basic Auth" value="basic" />
													<el-option label="API Key" value="apikey" />
												</el-select>
											</el-form-item>
											<template v-if="req.auth_type === 'bearer'">
												<el-form-item label="Token：">
													<el-input v-model="req.auth_token" placeholder="请输入 Bearer Token" style="width:400px" />
												</el-form-item>
											</template>
											<template v-if="req.auth_type === 'basic'">
												<el-form-item label="用户名：">
													<el-input v-model="req.auth_username" placeholder="请输入用户名" style="width:300px" />
												</el-form-item>
												<el-form-item label="密码：">
													<el-input v-model="req.auth_password" placeholder="请输入密码" type="password" show-password style="width:300px" />
												</el-form-item>
											</template>
											<template v-if="req.auth_type === 'apikey'">
												<el-form-item label="Key：">
													<el-input v-model="req.auth_key" placeholder="请输入 Key 名称" style="width:300px" />
												</el-form-item>
												<el-form-item label="Value：">
													<el-input v-model="req.auth_value" placeholder="请输入 Key 值" style="width:300px" />
												</el-form-item>
												<el-form-item label="添加到：">
													<el-radio-group v-model="req.auth_in">
														<el-radio value="header">Header</el-radio>
														<el-radio value="query">Query Params</el-radio>
													</el-radio-group>
												</el-form-item>
											</template>
										</el-form>
									</div>
								</el-tab-pane>
								<el-tab-pane name="before">
									<template #label>
										<el-badge :show-zero="false" :value="req.before.length" :offset="[10, 2]" type="danger">前置操作</el-badge>
									</template>
									<div class="op-pane">
										<div class="op-scroll">
											<el-collapse accordion>
												<el-collapse-item v-for="(pre, index) in req.before" :key="index">
													<template #title>
														<span style="display:flex;align-items:center">
															<el-button type="text" size="small" style="color:#f56c6c;margin-right:8px" @click.stop="removeBefore(index)"><el-icon><Delete /></el-icon></el-button>
															<span v-if="pre.type===1"><el-icon class="header-icon"><Connection /></el-icon>{{ index+1+'. 预请求接口：'+pre.title }}</span>
															<span v-if="pre.type===2"><el-icon class="header-icon"><Operation /></el-icon>{{ index+1+'. 预设变量：'+pre.name+' 赋值等于 '+pre.value }}</span>
															<span v-if="pre.type===3"><el-icon class="header-icon"><Clock /></el-icon>{{ index+1+'. 设置等待时长：'+pre.wait_time+'秒' }}</span>
															<span v-if="pre.type===4"><el-icon class="header-icon"><EditPen /></el-icon>{{ index+1+'. 自定义脚本：'+pre.title }}</span>
															<span v-if="pre.type===5"><el-icon class="header-icon"><Coin /></el-icon>{{ index+1+'. 数据库操作：'+(pre.db_name||'未选择数据库') }}</span>
															<span v-if="pre.type===6"><el-icon class="header-icon"><Document /></el-icon>{{ index+1+'. 脚本库：'+(pre.func_name||'未选择脚本') }}</span>
														</span>
													</template>
													<div v-if="pre.type===1">
														<el-form inline>
															<el-form-item label="操作名称："><el-input style="width:300px" v-model="pre.title" placeholder="请输入前置名称"></el-input></el-form-item>
															<el-form-item label="选择环境："><el-select placeholder="请选择环境" v-model="pre.env_id" style="width:300px"><el-option v-for="(env,i) in env_list" :key="i" :label="env.name" :value="env.id"></el-option></el-select></el-form-item>
															<el-form-item label="选择接口："><el-cascader :options="tree_list" v-model="pre.api_id" :props="{value:'id',label:'name',children:'children'}" style="width:705px"></el-cascader></el-form-item>
														</el-form>
													</div>
													<div v-if="pre.type===2">
														<el-form inline>
															<el-form-item label="变量名："><el-input style="width:200px" v-model="pre.name" placeholder="请输入变量名"></el-input></el-form-item>
															<el-form-item label="变量类型："><el-select placeholder="请选择变量类型" v-model="pre.env_type" style="width:200px"><el-option v-for="(t,i) in val_type_list" :key="i" :label="t.name" :value="t.value"></el-option></el-select></el-form-item>
															<el-form-item label="预期值："><el-input style="width:200px" v-model="pre.value" placeholder="请输入预期值"></el-input></el-form-item>
														</el-form>
													</div>
													<div v-if="pre.type===3"><el-form inline><el-form-item label="等待时间(秒)："><el-input-number style="width:200px" :min="0" :max="60" v-model="pre.wait_time"></el-input-number></el-form-item></el-form></div>
													<div v-if="pre.type===4">
														<div class="code-editor-wrap">
															<div class="code-editor-lang">Python</div>
															<textarea v-model="pre.code" class="code-textarea" placeholder="# 请输入 Python 代码" spellcheck="false" style="min-height:120px"></textarea>
														</div>
													</div>
													<div v-if="pre.type===5">
														<el-form inline>
															<el-form-item label="操作名称："><el-input v-model="pre.title" style="width:240px" placeholder="请输入操作名称" /></el-form-item>
															<el-form-item label="选择数据库："><el-select v-model="pre.db_id" style="width:240px" placeholder="请选择数据库" @change="(v) => { const db = local_db_list.find((d) => d.id===v); pre.db_name=db?.name||'' }"><el-option v-for="db in local_db_list" :key="db.id" :label="db.name" :value="db.id" /></el-select></el-form-item>
															<el-form-item label="SQL语句：" style="width:100%"><el-input v-model="pre.sql" type="textarea" :rows="4" placeholder="请输入SQL语句" style="width:600px;font-family:monospace;font-size:13px" /></el-form-item>
															<el-form-item label="结果提取变量："><el-input v-model="pre.result_var" style="width:240px" placeholder="将查询结果存入变量名（可选）" /></el-form-item>
														</el-form>
													</div>
													<div v-if="pre.type===6">
														<el-form inline>
															<el-form-item label="选择脚本："><el-select v-model="pre.func_id" style="width:300px" placeholder="请选择脚本库函数" filterable @change="(v) => { const fn = functionList.find((f) => f.id===v); pre.func_name=fn?.name||'' }"><el-option v-for="fn in functionList" :key="fn.id" :label="fn.name" :value="fn.id" /></el-select></el-form-item>
															<el-form-item label="传入参数（JSON）："><el-input v-model="pre.func_params" style="width:300px;font-family:monospace" placeholder='{"key":"value"}' /></el-form-item>
															<el-form-item label="结果存入变量："><el-input v-model="pre.result_var" style="width:200px" placeholder="变量名（可选）" /></el-form-item>
														</el-form>
													</div>
												</el-collapse-item>
											</el-collapse>
										</div>
										<div class="op-footer">
											<el-dropdown>
												<el-button type="primary" size="small">添加前置操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
												<template #dropdown>
													<el-dropdown-menu>
														<el-dropdown-item @click="addBefore(1)">预请求接口</el-dropdown-item>
														<el-dropdown-item @click="addBefore(2)">预设变量</el-dropdown-item>
														<el-dropdown-item @click="addBefore(3)">等待时长</el-dropdown-item>
														<el-dropdown-item @click="addBefore(4)">自定义脚本</el-dropdown-item>
														<el-dropdown-item @click="addBefore(5)">数据库操作</el-dropdown-item>
														<el-dropdown-item @click="addBefore(6)">脚本库</el-dropdown-item>
													</el-dropdown-menu>
												</template>
											</el-dropdown>
										</div>
									</div>
								</el-tab-pane>

								<!-- 后置操作 -->
								<el-tab-pane name="after">
									<template #label>
										<el-badge :show-zero="false" :value="req.after.length" :offset="[10, 2]" type="danger">后置操作</el-badge>
									</template>
									<div class="op-pane">
										<div class="op-scroll">
											<el-collapse accordion>
												<el-collapse-item v-for="(after, index) in req.after" :key="index">
													<template #title>
														<span style="display:flex;align-items:center">
															<el-button type="text" size="small" style="color:#f56c6c;margin-right:8px" @click.stop="removeAfter(index)"><el-icon><Delete /></el-icon></el-button>
															<span v-if="after.type===1"><el-icon class="header-icon"><Operation /></el-icon>{{ index+1+'. 提取变量：提取 '+after.name+' 赋值给 '+after.value }}</span>
															<span v-if="after.type===2"><el-icon class="header-icon"><Clock /></el-icon>{{ index+1+'. 设置等待时长：'+after.wait_time+'秒' }}</span>
															<span v-if="after.type===3"><el-icon class="header-icon"><CircleCheck /></el-icon>{{ index+1+'. 断言：'+(after.assert_name||'响应断言') }}</span>
															<span v-if="after.type===4"><el-icon class="header-icon"><Coin /></el-icon>{{ index+1+'. 数据库操作：'+(after.db_name||'未选择数据库') }}</span>
															<span v-if="after.type===5"><el-icon class="header-icon"><EditPen /></el-icon>{{ index+1+'. 自定义脚本' }}</span>
															<span v-if="after.type===6"><el-icon class="header-icon"><Document /></el-icon>{{ index+1+'. 脚本库：'+(after.func_name||'未选择脚本') }}</span>
															<span v-if="after.type===7"><el-icon class="header-icon"><Connection /></el-icon>{{ index+1+'. 从其他接口引入：'+(after.import_title||'未选择接口') }}</span>
														</span>
													</template>
													<div v-if="after.type===1">
														<el-form inline>
															<el-form-item><template #label><el-tooltip :content="tips" raw-content><el-button type="text" style="color:#000" :icon="InfoFilled"></el-button></el-tooltip>路径:</template><el-input style="width:300px" v-model="after.name" placeholder="请输入路径"></el-input></el-form-item>
															<el-form-item label="提取目标:"><el-select placeholder="请选择提取目标" v-model="after.res_type" style="width:300px"><el-option v-for="(r,i) in res_type_list" :key="i" :label="r.name" :value="r.value"></el-option></el-select></el-form-item>
															<el-form-item label="变量类型:"><el-select placeholder="请选择变量类型" v-model="after.env_type" style="width:300px"><el-option v-for="(t,i) in val_type_list" :key="i" :label="t.name" :value="t.value"></el-option></el-select></el-form-item>
															<el-form-item label="变量名:"><el-input style="width:300px" v-model="after.value" placeholder="请输入变量名"></el-input></el-form-item>
														</el-form>
													</div>
													<div v-if="after.type===2"><el-form inline><el-form-item label="等待时间(秒)："><el-input-number style="width:200px" :min="0" :max="60" v-model="after.wait_time"></el-input-number></el-form-item></el-form></div>
													<div v-if="after.type===3">
														<el-form inline>
															<el-form-item label="断言名称："><el-input v-model="after.assert_name" style="width:240px" placeholder="请输入断言名称" /></el-form-item>
															<el-form-item><template #label><el-tooltip :content="tips" raw-content><el-button type="text" style="color:#000" :icon="InfoFilled" /></el-tooltip>路径:</template><el-input v-model="after.assert_path" style="width:240px" placeholder="JSONPath 表达式" /></el-form-item>
															<el-form-item label="断言对象:"><el-select v-model="after.res_type" style="width:200px" placeholder="请选择"><el-option v-for="r in res_type_list" :key="r.value" :label="r.name" :value="r.value" /></el-select></el-form-item>
															<el-form-item label="预期值:"><el-input v-model="after.assert_value" style="width:240px" placeholder="请输入预期值" /></el-form-item>
														</el-form>
													</div>
													<div v-if="after.type===4">
														<el-form inline>
															<el-form-item label="操作名称："><el-input v-model="after.title" style="width:240px" placeholder="请输入操作名称" /></el-form-item>
															<el-form-item label="选择数据库："><el-select v-model="after.db_id" style="width:240px" placeholder="请选择数据库" @change="(v) => { const db = local_db_list.find((d) => d.id===v); after.db_name=db?.name||'' }"><el-option v-for="db in local_db_list" :key="db.id" :label="db.name" :value="db.id" /></el-select></el-form-item>
															<el-form-item label="SQL语句：" style="width:100%"><el-input v-model="after.sql" type="textarea" :rows="4" placeholder="请输入SQL语句" style="width:600px;font-family:monospace;font-size:13px" /></el-form-item>
															<el-form-item label="结果提取变量："><el-input v-model="after.result_var" style="width:240px" placeholder="将查询结果存入变量名（可选）" /></el-form-item>
														</el-form>
													</div>
													<div v-if="after.type===5">
														<div class="code-editor-wrap">
															<div class="code-editor-lang">Python</div>
															<textarea v-model="after.code" class="code-textarea" placeholder="# 请输入 Python 代码" spellcheck="false" style="min-height:120px"></textarea>
														</div>
													</div>
													<div v-if="after.type===6">
														<el-form inline>
															<el-form-item label="选择脚本："><el-select v-model="after.func_id" style="width:300px" placeholder="请选择脚本库函数" filterable @change="(v) => { const fn = functionList.find((f) => f.id===v); after.func_name=fn?.name||'' }"><el-option v-for="fn in functionList" :key="fn.id" :label="fn.name" :value="fn.id" /></el-select></el-form-item>
															<el-form-item label="传入参数（JSON）："><el-input v-model="after.func_params" style="width:300px;font-family:monospace" placeholder='{"key":"value"}' /></el-form-item>
															<el-form-item label="结果存入变量："><el-input v-model="after.result_var" style="width:200px" placeholder="变量名（可选）" /></el-form-item>
														</el-form>
													</div>
													<div v-if="after.type===7">
														<el-form inline>
															<el-form-item label="操作名称："><el-input v-model="after.import_title" style="width:240px" placeholder="请输入名称" /></el-form-item>
															<el-form-item label="选择环境："><el-select v-model="after.env_id" style="width:240px" placeholder="请选择环境"><el-option v-for="env in env_list" :key="env.id" :label="env.name" :value="env.id" /></el-select></el-form-item>
															<el-form-item label="选择接口："><el-cascader :options="tree_list" v-model="after.api_id" :props="{value:'id',label:'name',children:'children'}" style="width:500px" placeholder="请选择接口" /></el-form-item>
														</el-form>
													</div>
												</el-collapse-item>
											</el-collapse>
										</div>
										<div class="op-footer">
											<el-dropdown>
												<el-button type="primary" size="small">添加后置操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
												<template #dropdown>
													<el-dropdown-menu>
														<el-dropdown-item @click="addAfter(1)">提取变量</el-dropdown-item>
														<el-dropdown-item @click="addAfter(2)">等待时长</el-dropdown-item>
														<el-dropdown-item @click="addAfter(3)">断言</el-dropdown-item>
														<el-dropdown-item @click="addAfter(4)">数据库操作</el-dropdown-item>
														<el-dropdown-item @click="addAfter(5)">自定义脚本</el-dropdown-item>
														<el-dropdown-item @click="addAfter(6)">脚本库</el-dropdown-item>
														<el-dropdown-item @click="addAfter(7)">从其他接口引入</el-dropdown-item>
													</el-dropdown-menu>
												</template>
											</el-dropdown>
										</div>
									</div>
								</el-tab-pane>

								<!-- 断言 -->
								<el-tab-pane name="assert">
									<template #label>
										<el-badge :show-zero="false" :value="req.assert.length" :offset="[10, 2]" type="danger">断言</el-badge>
									</template>
									<div class="op-pane">
										<div class="op-scroll">
											<el-collapse accordion>
												<el-collapse-item v-for="(assert, index) in req.assert" :key="index">
													<template #title>
														<span style="display:flex;align-items:center">
															<el-button type="text" size="small" style="color:#f56c6c;margin-right:8px" @click.stop="removeAssert(index)"><el-icon><Delete /></el-icon></el-button>
															<span v-if="assert.type===1"><el-icon class="header-icon"><CircleCheck /></el-icon>{{ index+1+'. 响应断言：断言 '+assert.name+' 等于 '+assert.value }}</span>
															<span v-if="assert.type===2"><el-icon class="header-icon"><Coin /></el-icon>{{ index+1+'. Db断言：查询表 '+assert.ops_db_table+' 条件：'+assert.ops_db_where }}</span>
															<span v-if="assert.type===3"><el-icon class="header-icon"><Coin /></el-icon>{{ index+1+'. Redis断言：查询key '+assert.ops_redis_key }}</span>
															<span v-if="assert.type===4"><el-icon class="header-icon"><Coin /></el-icon>{{ index+1+'. 直连-数据库断言：查询表 '+assert.local_db_table+' 条件：'+assert.local_db_where }}</span>
															<span v-if="assert.type===5"><el-icon class="header-icon"><EditPen /></el-icon>{{ index+1+'. 自定义断言' }}</span>
														</span>
													</template>
													<div v-if="assert.type===1">
														<el-form inline>
															<el-form-item label="路径:"><el-input style="width:220px" v-model="assert.name" placeholder="如 $.code"></el-input></el-form-item>
															<el-form-item label="断言对象:"><el-select placeholder="请选择断言对象" v-model="assert.res_type" style="width:220px"><el-option v-for="(r,i) in res_type_list" :key="i" :label="r.name" :value="r.value"></el-option></el-select></el-form-item>
															<el-form-item label="预期值:"><el-input style="width:220px" v-model="assert.value" placeholder="请输入预期值"></el-input></el-form-item>
														</el-form>
													</div>
													<div v-if="assert.type===2">
														<el-form inline>
															<el-form-item label="查询表："><el-input v-model="assert.ops_db_table" style="width:200px" placeholder="表名" /></el-form-item>
															<el-form-item label="查询条件："><el-input v-model="assert.ops_db_where" style="width:300px" placeholder="WHERE 条件，如 id=1" /></el-form-item>
															<el-form-item label="断言字段：" style="width:100%">
																<div v-for="(a,ai) in (assert.ops_db_assert||[])" :key="ai" style="display:flex;gap:8px;margin-bottom:6px">
																	<el-input v-model="a.field" placeholder="字段名" style="width:160px" size="small" />
																	<el-input v-model="a.value" placeholder="预期值" style="width:200px" size="small" />
																	<el-button type="danger" link size="small" @click="assert.ops_db_assert.splice(ai,1)">删除</el-button>
																</div>
																<el-button type="primary" link size="small" @click="assert.ops_db_assert.push({field:'',value:''})">+ 添加断言字段</el-button>
															</el-form-item>
														</el-form>
													</div>
													<div v-if="assert.type===4">
														<el-form inline>
															<el-form-item label="选择数据库："><el-select v-model="assert.local_db" style="width:220px" placeholder="请选择数据库"><el-option v-for="db in local_db_list" :key="db.id" :label="db.name" :value="db.id" /></el-select></el-form-item>
															<el-form-item label="查询表："><el-input v-model="assert.local_db_table" style="width:200px" placeholder="表名" /></el-form-item>
															<el-form-item label="查询条件："><el-input v-model="assert.local_db_where" style="width:300px" placeholder="WHERE 条件，如 id=1" /></el-form-item>
															<el-form-item label="断言字段：" style="width:100%">
																<div v-for="(a,ai) in (assert.local_db_assert||[])" :key="ai" style="display:flex;gap:8px;margin-bottom:6px">
																	<el-input v-model="a.field" placeholder="字段名" style="width:160px" size="small" />
																	<el-input v-model="a.value" placeholder="预期值" style="width:200px" size="small" />
																	<el-button type="danger" link size="small" @click="assert.local_db_assert.splice(ai,1)">删除</el-button>
																</div>
																<el-button type="primary" link size="small" @click="assert.local_db_assert.push({field:'',value:''})">+ 添加断言字段</el-button>
															</el-form-item>
														</el-form>
													</div>
													<div v-if="assert.type===5">
														<el-form label-width="90px">
															<el-form-item label="断言名称："><el-input v-model="assert.custom_name" style="width:300px" placeholder="请输入断言名称" /></el-form-item>
															<el-form-item label="断言脚本："><el-input v-model="assert.custom_script" type="textarea" :rows="6" placeholder="请输入断言脚本（Python），可使用 response、status_code、headers 等变量" style="width:600px;font-family:monospace;font-size:13px" /></el-form-item>
															<el-form-item label="预期结果："><el-input v-model="assert.custom_expect" style="width:300px" placeholder="预期返回值（可选）" /></el-form-item>
														</el-form>
													</div>
												</el-collapse-item>
											</el-collapse>
										</div>
										<div class="op-footer">
											<el-dropdown>
												<el-button type="primary" size="small">添加断言 <el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
												<template #dropdown>
													<el-dropdown-menu>
														<el-dropdown-item @click="addAssert(1)"><el-icon><CircleCheck /></el-icon>响应结果断言</el-dropdown-item>
														<el-dropdown-item @click="addAssert(2)"><el-icon><Coin /></el-icon>Db断言</el-dropdown-item>
														<el-dropdown-item @click="addAssert(3)"><el-icon><Coin /></el-icon>Redis断言</el-dropdown-item>
														<el-dropdown-item @click="addAssert(4)"><el-icon><Coin /></el-icon>直连-数据库断言</el-dropdown-item>
														<el-dropdown-item @click="addAssert(5)"><el-icon><EditPen /></el-icon>自定义断言</el-dropdown-item>
													</el-dropdown-menu>
												</template>
											</el-dropdown>
										</div>
									</div>
								</el-tab-pane>
								<!-- 配置 -->
								<el-tab-pane label="配置" name="config">
									<div>
										<el-form v-model="req.config" label-position="right">
											<el-form-item label="重试次数(次)："><el-input-number v-model="req.config.retry"></el-input-number></el-form-item>
											<el-form-item label="接口连接超时(秒)："><el-input-number v-model="req.config.req_timeout"></el-input-number></el-form-item>
											<el-form-item label="结果读取超时(秒)："><el-input-number v-model="req.config.res_timeout"></el-input-number></el-form-item>
										</el-form>
									</div>
								</el-tab-pane>
								<!-- 设置 -->
								<el-tab-pane label="设置" name="settings">
									<div class="settings-pane">
										<div class="settings-item">
											<div class="settings-label">
												<span>SSL 证书验证</span>
												<el-tooltip content="关闭后跳过 HTTPS 证书校验，适用于自签名证书环境" placement="top">
													<el-icon class="settings-help"><InfoFilled /></el-icon>
												</el-tooltip>
											</div>
											<div style="display:flex;align-items:center;gap:10px">
												<el-button link size="small" style="color:#409eff;font-size:12px" @click="certDialogVisible=true">证书管理</el-button>
												<el-switch v-model="req.config.ssl_verify" />
											</div>
										</div>
										<div class="settings-item">
											<div class="settings-label">
												<span>自动跟随重定向</span>
												<el-tooltip content="开启后自动跟随 3xx 重定向响应" placement="top">
													<el-icon class="settings-help"><InfoFilled /></el-icon>
												</el-tooltip>
											</div>
											<el-switch v-model="req.config.allow_redirects" />
										</div>
										<div class="settings-item">
											<div class="settings-label">
												<span>URL 自动编码</span>
												<el-tooltip content="发送前对 URL 中的特殊字符进行 percent-encoding" placement="top">
													<el-icon class="settings-help"><InfoFilled /></el-icon>
												</el-tooltip>
											</div>
											<el-switch v-model="req.config.url_encode" />
										</div>
									</div>
								</el-tab-pane>
							</el-tabs>
						</div>
					</div>

				<!-- 证书管理弹窗 -->
				<el-dialog v-model="certDialogVisible" title="证书管理" width="560px" destroy-on-close class="cert-dialog">
					<div v-if="certPage==='list'">
						<!-- CA 证书 -->
						<div class="cert-section">
							<div class="cert-section-header">
								<div>
									<div class="cert-section-title">CA 证书</div>
									<div class="cert-section-sub">选择信任的 CA 证书</div>
								</div>
								<el-switch v-model="caEnabled" active-text="开启" />
							</div>
							<div v-if="caEnabled" class="cert-field-row">
								<span class="cert-field-label">PEM 文件</span>
								<el-upload :show-file-list="false" :auto-upload="false" :on-change="onCaFileChange" accept=".pem,.crt,.cer">
									<el-button size="small" plain>{{ caFileName || '请选择文件' }}</el-button>
								</el-upload>
							</div>
						</div>
						<!-- 客户端证书 -->
						<div class="cert-section" style="margin-top:20px">
							<div class="cert-section-header">
								<div>
									<div class="cert-section-title">客户端证书</div>
									<div class="cert-section-sub">添加或管理 SSL 证书</div>
								</div>
								<el-button link size="small" style="color:#409eff" @click="certPage='add'">添加客户端证书</el-button>
							</div>
							<div v-if="clientCerts.length===0" class="cert-empty">暂无客户端证书</div>
							<div v-for="(c,i) in clientCerts" :key="i" class="cert-client-item">
								<div>
									<span class="cert-client-domain">{{ c.host }}:{{ c.port }}</span>
									<span v-if="c.crt" class="cert-client-tag">CRT</span>
									<span v-if="c.pfx" class="cert-client-tag">PFX</span>
								</div>
								<el-button type="danger" link size="small" @click="clientCerts.splice(i,1)">删除</el-button>
							</div>
						</div>
					</div>
					<!-- 添加证书子页面 -->
					<div v-else>
						<div class="cert-breadcrumb">
							<el-button link size="small" @click="certPage='list'">客户端证书</el-button>
							<span style="color:#909399;margin:0 4px">/</span>
							<span style="color:#303133;font-size:13px">添加证书</span>
						</div>
						<el-form :model="newCert" label-width="90px" style="margin-top:16px">
							<el-form-item label="域名">
								<div style="display:flex;align-items:center;gap:6px;width:100%">
									<el-input v-model="newCert.host" placeholder="example.com" style="flex:1" />
									<span style="color:#909399">:</span>
									<el-input v-model="newCert.port" placeholder="443" style="width:90px" />
								</div>
							</el-form-item>
							<el-form-item label="CRT 文件">
								<el-upload :show-file-list="false" :auto-upload="false" :on-change="(f:any)=>newCert.crt=f.name" accept=".crt,.cer,.pem">
									<el-button size="small" plain>{{ newCert.crt || '请选择文件' }}</el-button>
								</el-upload>
							</el-form-item>
							<el-form-item label="KEY 文件">
								<el-upload :show-file-list="false" :auto-upload="false" :on-change="(f:any)=>newCert.key=f.name" accept=".key,.pem">
									<el-button size="small" plain>{{ newCert.key || '请选择文件' }}</el-button>
								</el-upload>
							</el-form-item>
							<el-form-item label="PFX 文件">
								<el-upload :show-file-list="false" :auto-upload="false" :on-change="(f:any)=>newCert.pfx=f.name" accept=".pfx,.p12">
									<el-button size="small" plain>{{ newCert.pfx || '请选择文件' }}</el-button>
								</el-upload>
							</el-form-item>
							<el-form-item label="密钥">
								<el-input v-model="newCert.passphrase" type="password" show-password placeholder="证书密钥（可选）" />
							</el-form-item>
						</el-form>
						<div style="display:flex;gap:10px;margin-top:8px">
							<el-button type="primary" @click="addClientCert">添加</el-button>
							<el-button @click="certPage='list'">取消</el-button>
						</div>
					</div>
				</el-dialog>

				<!-- 保存为用例弹窗 -->
				<el-dialog v-model="saveCaseDialogVisible" title="保存为用例" width="480px" destroy-on-close>
					<el-form :model="saveCaseForm" label-width="80px">
						<el-form-item label="用例名称" required>
							<el-input v-model="saveCaseForm.name" placeholder="请输入用例名称" />
						</el-form-item>
						<el-form-item label="用例类型">
							<el-radio-group v-model="saveCaseForm.case_type">
								<el-radio-button v-for="t in caseTypeOptions" :key="t.value" :value="t.value">{{ t.label }}</el-radio-button>
							</el-radio-group>
						</el-form-item>
						<el-form-item label="描述">
							<el-input v-model="saveCaseForm.description" type="textarea" :rows="2" placeholder="可选" />
						</el-form-item>
						<el-form-item label="用例集" required>
							<div v-loading="saveCaseLoading" style="width:100%;min-height:40px">
								<div v-if="!saveCaseLoading && !saveCaseSuiteTree.length" style="display:flex;align-items:center;gap:8px;color:var(--el-text-color-placeholder);font-size:13px">
									<span>该服务暂无用例集，请先在用例管理中创建</span>
									<el-button link size="small" @click="reloadSuiteTree">刷新</el-button>
								</div>
								<el-tree
									v-if="!saveCaseLoading && saveCaseSuiteTree.length"
									:data="saveCaseSuiteTree"
									:props="{ label: 'name', children: 'children' }"
									node-key="id"
									highlight-current
									default-expand-all
									:expand-on-click-node="false"
									style="border:1px solid var(--el-border-color);border-radius:6px;padding:6px;max-height:220px;overflow-y:auto"
									@node-click="(d:any) => saveCaseForm.suite_id = d.id"
								>
									<template #default="{ data }">
										<span :style="saveCaseForm.suite_id===data.id?'color:#409eff;font-weight:600':''">
											<el-icon style="margin-right:4px;color:#f39c12"><Folder /></el-icon>{{ data.name }}
										</span>
									</template>
								</el-tree>
								<div v-if="saveCaseForm.suite_id" style="margin-top:6px;font-size:12px;color:#409eff">
									已选用例集 ID: {{ saveCaseForm.suite_id }}
								</div>
							</div>
						</el-form-item>
					</el-form>
					<template #footer>
						<el-button @click="saveCaseDialogVisible=false">取消</el-button>
						<el-button type="primary" :loading="saveCaseSubmitting" @click="confirmSaveAsCase">保存</el-button>
					</template>
				</el-dialog>

				<!-- 响应区 -->
				<div class="response-section">
					<div class="panel-card">
						<div class="res-tab-header">
							<el-tabs v-model="res_active" class="apifox-tabs res-tabs" style="flex:1;min-width:0">
								<el-tab-pane label="Body" name="res" />
								<el-tab-pane name="res_cookies"><template #label><el-badge :show-zero="false" :value="(res.cookies||[]).length" :offset="[8,0]" type="primary" class="res-badge">Cookie</el-badge></template></el-tab-pane>
								<el-tab-pane label="Header" name="res_log" />
								<el-tab-pane label="控制台" name="res_console" />
								<el-tab-pane label="实际请求" name="res_raw" />
								<el-tab-pane name="before_res"><template #label><el-badge :show-zero="false" :value="res.before.length" :offset="[8,0]" type="danger" class="res-badge">前置操作结果</el-badge></template></el-tab-pane>
								<el-tab-pane name="after_res"><template #label><el-badge :show-zero="false" :value="res.after.length" :offset="[8,0]" type="danger" class="res-badge">后置操作结果</el-badge></template></el-tab-pane>
								<el-tab-pane name="assert_res"><template #label><el-badge :show-zero="false" :value="res.assert.length" :offset="[8,0]" type="danger" class="res-badge">断言结果</el-badge></template></el-tab-pane>
							</el-tabs>
							<div class="res-meta">
								<el-tag v-if="res.code>0" size="small" :type="res.code>=200&&res.code<300?'success':res.code>=400?'danger':'warning'" effect="light" class="res-meta-tag">{{ res.code }}</el-tag>
								<el-tag v-if="res.res_time>0" size="small" type="info" effect="plain" class="res-meta-tag">{{ res.res_time }} ms</el-tag>
								<el-tag v-if="res.size>0" size="small" type="info" effect="plain" class="res-meta-tag">{{ res.size >= 1024 ? (res.size/1024).toFixed(1)+'KB' : res.size+'B' }}</el-tag>
							</div>
						</div>
						<div class="res-content">
							<template v-if="res_active==='res'">
								<div class="res-code-panel">
									<div class="res-code-toolbar">
										<button class="res-copy-btn" :class="{copied: bodyCopied}" @click="copyBody" title="复制响应内容">
											<svg v-if="!bodyCopied" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
											<svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
											<span>{{ bodyCopied ? '已复制' : '复制' }}</span>
										</button>
									</div>
									<vue-json-pretty v-model:data="res.body" :height="resJsonHeight" :showIcon="true" :showLine="true" :virtual="true" :showSelectController="true" class="res-json-pretty" />
								</div>
							</template>
							<template v-else-if="res_active==='res_cookies'">
								<div class="res-dark-kv-panel">
									<div v-if="!(res.cookies&&res.cookies.length)" class="res-dark-empty">暂无 Cookie</div>
									<table v-else class="res-dark-kv-table">
										<thead><tr><th>Name</th><th>Value</th><th>Domain</th><th>Path</th><th>Expires</th><th>Secure</th></tr></thead>
										<tbody><tr v-for="(c,i) in res.cookies" :key="i"><td class="res-dark-key">{{ c.name }}</td><td class="res-dark-val">{{ c.value }}</td><td class="res-dark-muted">{{ c.domain||"-" }}</td><td class="res-dark-muted">{{ c.path||"/" }}</td><td class="res-dark-muted">{{ c.expires||"-" }}</td><td class="res-dark-muted">{{ c.secure?"✓":"-" }}</td></tr></tbody>
									</table>
								</div>
							</template>
							<template v-else-if="res_active==='res_log'">
								<div class="res-dark-kv-panel">
									<div v-if="!res.header||!Object.keys(res.header).length" class="res-dark-empty">暂无 Header</div>
									<table v-else class="res-dark-kv-table">
										<thead><tr><th>Name</th><th>Value</th></tr></thead>
										<tbody><tr v-for="(v,k) in res.header" :key="k"><td class="res-dark-key">{{ k }}</td><td class="res-dark-val">{{ v }}</td></tr></tbody>
									</table>
								</div>
							</template>
							<template v-else-if="res_active==='res_console'">
								<div class="res-console-panel">
									<div v-if="!(res.console&&res.console.length)" class="res-dark-empty">暂无控制台输出</div>
									<div v-for="(log,i) in (res.console||[])" :key="i" class="res-console-line" :class="'console-'+log.level">{{ log.msg }}</div>
								</div>
							</template>
							<template v-else-if="res_active==='res_raw'">
								<div class="res-raw-panel">
									<div class="res-raw-toolbar">
										<span v-for="lang in rawLangs" :key="lang.value" class="raw-lang-item" :class="{active: rawLang===lang.value}" @click="rawLang=lang.value">{{ lang.label }}</span>
									</div>
									<div class="res-raw-editor">
										<div v-if="!res.raw_request" class="res-dark-empty">发送请求后显示实际请求内容</div>
										<pre v-else class="res-raw-code"><code>{{ buildRawCode(res.raw_request, rawLang) }}</code></pre>
									</div>
								</div>
							</template>
							<template v-else-if="res_active==='before_res'">
								<div class="res-ops-panel">
									<div v-if="!res.before||!res.before.length" class="res-dark-empty">暂无前置操作结果</div>
									<div v-for="(b,i) in res.before" :key="i" class="res-ops-item">
										<div class="res-ops-title" :class="b.status===1?'ops-ok':'ops-fail'">
											<span class="ops-icon">{{ b.status===1?"✓":"✗" }}</span>
											<span>{{ i+1+'. '+b.message }}</span>
										</div>
										<div v-if="b.type===1&&b.content" class="res-ops-body">
											<vue-json-pretty v-model:data="b.content.body" :height="160" :showIcon="true" :showLine="true" :virtual="true" :showSelectController="true" class="res-json-pretty" />
										</div>
									</div>
								</div>
							</template>
							<template v-else-if="res_active==='after_res'">
								<div class="res-ops-panel">
									<div v-if="!res.after||!res.after.length" class="res-dark-empty">暂无后置操作结果</div>
									<div v-for="(a,i) in res.after" :key="i" class="res-ops-item">
										<div class="res-ops-title" :class="a.status===1?'ops-ok':'ops-fail'">
											<span class="ops-icon">{{ a.status===1?"✓":"✗" }}</span>
											<span>{{ i+1+'. '+a.message }}</span>
										</div>
									</div>
								</div>
							</template>
							<template v-else-if="res_active==='assert_res'">
								<div class="res-ops-panel">
									<div v-if="!res.assert||!res.assert.length" class="res-dark-empty">暂无断言结果</div>
									<div v-for="(a,i) in res.assert" :key="i" class="res-ops-item">
										<div class="res-ops-title" :class="a.status===1?'ops-ok':'ops-fail'">
											<span class="ops-icon">{{ a.status===1?"✓":"✗" }}</span>
											<span>{{ i+1+'. '+a.message }}</span>
										</div>
									</div>
								</div>
							</template>
						</div>
					</div>
				</div>
				</div>
			</div>

			<!-- 接口文档面板 -->
			<div v-show="mainTab==='doc'" class="side-panel doc-panel">
				<template v-if="docInfo">
					<!-- 标题栏 -->
					<div class="doc-header">
						<div class="doc-header-left">
							<span class="doc-method-badge" :style="{background: currentMethodColor}">{{ docInfo.methodName }}</span>
							<span class="doc-path">{{ docInfo.url }}</span>
						</div>
						<div class="doc-header-right">
							<el-tag size="small" effect="plain" type="info">{{ docInfo.name }}</el-tag>
						</div>
					</div>
					<div v-if="docInfo.description" class="doc-desc-block">{{ docInfo.description }}</div>

					<!-- 请求参数 -->
					<div v-if="docInfo.parameters&&docInfo.parameters.length" class="doc-section">
						<div class="doc-section-title">请求参数</div>
						<table class="doc-table">
							<thead><tr><th>参数名</th><th>位置</th><th>类型</th><th>必填</th><th>说明</th></tr></thead>
							<tbody>
								<tr v-for="p in docInfo.parameters" :key="p.name">
									<td class="doc-param-name">{{ p.name }}</td>
									<td><span class="doc-in-badge" :class="'in-'+p.in">{{ p.in }}</span></td>
									<td class="doc-type">{{ p.schema?.type || p.type || '-' }}</td>
									<td><el-tag v-if="p.required" size="small" type="danger" effect="plain">必填</el-tag><span v-else class="doc-optional">可选</span></td>
									<td class="doc-desc-cell">{{ p.description || '-' }}</td>
								</tr>
							</tbody>
						</table>
					</div>

					<!-- 请求体 -->
					<div v-if="docInfo.requestBody" class="doc-section">
						<div class="doc-section-title">请求体</div>
						<div class="doc-content-type">Content-Type: <code>{{ docInfo.requestBodyType }}</code></div>
						<table v-if="docInfo.requestBodyFields&&docInfo.requestBodyFields.length" class="doc-table">
							<thead><tr><th>字段名</th><th>类型</th><th>必填</th><th>说明</th></tr></thead>
							<tbody>
								<tr v-for="f in docInfo.requestBodyFields" :key="f.name">
									<td class="doc-param-name">{{ f.name }}</td>
									<td class="doc-type">{{ f.type || '-' }}</td>
									<td><el-tag v-if="f.required" size="small" type="danger" effect="plain">必填</el-tag><span v-else class="doc-optional">可选</span></td>
									<td class="doc-desc-cell">{{ f.description || '-' }}</td>
								</tr>
							</tbody>
						</table>
						<div v-else class="doc-raw-schema">
							<pre class="doc-pre">{{ docInfo.requestBodyRaw }}</pre>
						</div>
					</div>

					<!-- 响应 -->
					<div v-if="docInfo.responses&&docInfo.responses.length" class="doc-section">
						<div class="doc-section-title">返回响应</div>
						<div v-for="resp in docInfo.responses" :key="resp.code" class="doc-response-item">
							<div class="doc-response-header">
								<el-tag size="small" :type="resp.code>=200&&resp.code<300?'success':resp.code>=400?'danger':'warning'" effect="light">{{ resp.code }}</el-tag>
								<span class="doc-response-desc">{{ resp.description }}</span>
							</div>
							<div v-if="resp.fields&&resp.fields.length" style="margin-top:8px">
								<table class="doc-table">
									<thead><tr><th>字段名</th><th>类型</th><th>说明</th></tr></thead>
									<tbody>
										<tr v-for="f in resp.fields" :key="f.name">
											<td class="doc-param-name">{{ f.name }}</td>
											<td class="doc-type">{{ f.type || '-' }}</td>
											<td class="doc-desc-cell">{{ f.description || '-' }}</td>
										</tr>
									</tbody>
								</table>
							</div>
							<div v-else-if="resp.example" class="doc-raw-schema">
								<pre class="doc-pre">{{ resp.example }}</pre>
							</div>
						</div>
					</div>
				</template>
				<div v-else class="side-panel-empty">
					<el-icon style="font-size:40px;color:#dcdfe6"><Document /></el-icon>
					<p>暂无接口文档，请先拉取 Swagger / Apifox 文档</p>
				</div>
			</div>

			<!-- 调试记录面板 -->
			<div v-show="mainTab==='history'" class="side-panel">
				<div class="side-panel-toolbar">
					<el-button size="small" @click="loadDebugHistory">刷新</el-button>
				</div>
				<div v-if="!debugRecordList.length" class="side-panel-empty">
					<el-icon style="font-size:40px;color:#dcdfe6"><Document /></el-icon>
					<p>暂无调试记录</p>
				</div>
				<div v-else class="history-list">
					<div v-for="(r,i) in debugRecordList" :key="i" class="history-item">
						<div class="history-item-left">
							<el-tag size="small" :type="r.status_code>=200&&r.status_code<300?'success':r.status_code>=400?'danger':'warning'" effect="light">{{ r.status_code }}</el-tag>
							<span class="history-url">{{ r.req?.url || '-' }}</span>
						</div>
						<span class="history-time">{{ r.create_time ? String(r.create_time).replace('T',' ') : '' }}</span>
					</div>
				</div>
			</div>

			<!-- Mock 面板 -->
			<div v-show="mainTab==='mock'" class="side-panel mock-panel">
				<!-- Mock 地址 -->
				<div class="mock-section">
					<div class="mock-section-title">Mock 地址</div>
					<div class="mock-addr-bar">
						<code class="mock-url">{{ mockBaseUrl }}/mock{{ req.url || '/api/path' }}</code>
						<el-button size="small" plain @click="copyMockUrl">复制</el-button>
					</div>
				</div>
				<!-- Mock 期望 -->
				<div class="mock-section" style="margin-top:20px">
					<div class="mock-section-header">
						<span class="mock-section-title">Mock 期望</span>
						<el-button size="small" type="primary" plain @click="addMockExpect">+ 新建期望</el-button>
					</div>
					<el-table :data="mockExpects" size="small" style="margin-top:8px" empty-text="暂无期望">
						<el-table-column prop="name" label="名称" />
						<el-table-column prop="condition" label="条件" />
						<el-table-column label="操作" width="100">
							<template #default="{$index}">
								<el-button type="danger" link size="small" @click="mockExpects.splice($index,1)">删除</el-button>
							</template>
						</el-table-column>
					</el-table>
				</div>
				<!-- Mock 脚本 -->
				<div class="mock-section" style="margin-top:20px">
					<div class="mock-section-header">
						<span class="mock-section-title">Mock 脚本</span>
						<el-switch v-model="mockScriptEnabled" size="small" />
					</div>
					<div v-if="mockScriptEnabled" style="margin-top:10px">
						<div class="code-editor-wrap">
							<div class="code-editor-lang">JavaScript</div>
							<textarea v-model="mockScript" class="code-textarea" placeholder="// 在此编写 Mock 脚本&#10;// 例：mock.mockResponse({ code: 200, data: {} })" spellcheck="false" style="min-height:120px"></textarea>
						</div>
					</div>
				</div>
			</div>

			<!-- 新建 Mock 期望弹窗 -->
			<el-dialog v-model="mockExpectDialogVisible" title="新建 Mock 期望" width="480px" destroy-on-close>
				<el-form :model="newMockExpect" label-width="80px">
					<el-form-item label="名称"><el-input v-model="newMockExpect.name" placeholder="期望名称" /></el-form-item>
					<el-form-item label="条件"><el-input v-model="newMockExpect.condition" placeholder="匹配条件（可选）" /></el-form-item>
					<el-form-item label="响应体">
						<div class="code-editor-wrap" style="width:100%">
							<div class="code-editor-lang">JSON</div>
							<textarea v-model="newMockExpect.body" class="code-textarea" placeholder='{"code":200,"data":{}}' spellcheck="false" style="min-height:100px"></textarea>
						</div>
					</el-form-item>
					<el-form-item label="状态码"><el-input-number v-model="newMockExpect.status" :min="100" :max="599" /></el-form-item>
				</el-form>
				<template #footer>
					<el-button @click="mockExpectDialogVisible=false">取消</el-button>
					<el-button type="primary" @click="confirmAddMockExpect">确定</el-button>
				</template>
			</el-dialog>

		</el-card>
	</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import VueJsonPretty from 'vue-json-pretty';
import JsonEditor from '/@/components/code-editor/JsonEditor.vue';
import 'vue-json-pretty/lib/styles.css';
import { ArrowDown, Operation, Clock, CircleCheck, Coin, Delete, Connection, EditPen, Document, InfoFilled, View, Folder } from '@element-plus/icons-vue';
import { api_send, save_api, save_api_case, req_history, edit_history, api_params, apiAutomationApi } from '/@/api/v1/api_automation';
import { useFileApi } from '/@/api/v1/common/file';
import { ElMessage, ElMessageBox } from 'element-plus';

const props = defineProps({
	apiData: { type: Object, default: () => ({}) },
	envId: { type: [Number, String], default: null },
	env_list: { type: Array, default: () => [] },
	tree_list: { type: Array, default: () => [] },
	redis_example_list: { type: Array, default: () => ['common'] },
	local_db_list: { type: Array, default: () => [] },
	params_list: { type: Array, default: () => [{ name: '', id: null }] },
	serviceId: { type: [Number, String], default: null },
	embedded: { type: Boolean, default: false }, // 嵌入模式：隐藏顶部大 Tab
	initialTab: { type: String, default: 'debug' }, // 嵌入模式下初始显示的 Tab
});

const emit = defineEmits(['caseSaved', 'apiSaved']);
const fileApi = useFileApi();

const req_active = ref<any>('body');
const res_active = ref<any>('res');
const bodyCopied = ref(false);
const copyBody = () => {
	const text = typeof res.value.body === 'string' ? res.value.body : JSON.stringify(res.value.body, null, 2);
	navigator.clipboard?.writeText(text).then(() => {
		bodyCopied.value = true;
		setTimeout(() => { bodyCopied.value = false; }, 2000);
	});
};
const rawLang = ref('curl');
const rawLangs = [
	{ label: 'cURL', value: 'curl' },
	{ label: 'Python', value: 'python' },
	{ label: 'JavaScript', value: 'javascript' },
	{ label: 'Java', value: 'java' },
	{ label: 'Go', value: 'go' },
	{ label: 'PHP', value: 'php' },
	{ label: 'HTTP', value: 'http' },
];
const buildRawCode = (raw: any, lang: string): string => {
	if (!raw) return '';
	const method = raw.method || 'GET';
	const url = raw.url || '';
	const headers: Record<string,string> = raw.headers || {};
	const body = raw.body || '';
	const headerStr = Object.entries(headers).map(([k,v]) => `${k}: ${v}`).join('\n');
	const curlHeaders = Object.entries(headers).map(([k,v]) => `  --header '${k}: ${v}' \\`).join('\n');
	const bodyStr = typeof body === 'string' ? body : JSON.stringify(body, null, 2);
	if (lang === 'curl') {
		const bodyPart = bodyStr ? `\n  --data '${bodyStr.replace(/'/g,"'\\''")}'` : '';
		return `curl --location --request ${method} '${url}' \\\n${curlHeaders}${bodyPart}`;
	}
	if (lang === 'python') {
		const hLines = Object.entries(headers).map(([k,v]) => `    "${k}": "${v}",`).join('\n');
		const bLine = bodyStr ? `\npayload = ${bodyStr}\n` : '\npayload = None\n';
		return `import requests\n\nurl = "${url}"\nheaders = {\n${hLines}\n}\n${bLine}\nresponse = requests.request("${method}", url, headers=headers, data=payload)\nprint(response.text)`;
	}
	if (lang === 'javascript') {
		const hLines = Object.entries(headers).map(([k,v]) => `  "${k}": "${v}",`).join('\n');
		const bLine = bodyStr ? `\n  body: JSON.stringify(${bodyStr}),` : '';
		return `fetch("${url}", {\n  method: "${method}",\n  headers: {\n${hLines}\n  },${bLine}\n})\n  .then(r => r.json())\n  .then(console.log);`;
	}
	if (lang === 'java') {
		return `OkHttpClient client = new OkHttpClient();\nRequest request = new Request.Builder()\n  .url("${url}")\n  .method("${method}", ${bodyStr ? `RequestBody.create("${bodyStr}", MediaType.parse("application/json"))` : 'null'})\n  .build();\nResponse response = client.newCall(request).execute();`;
	}
	if (lang === 'go') {
		const bLine = bodyStr ? `\npayload := strings.NewReader(\`${bodyStr}\`)` : '\nvar payload io.Reader';
		return `package main\nimport (\n  "fmt"\n  "net/http"\n  "strings"\n)\nfunc main() {${bLine}\n  req, _ := http.NewRequest("${method}", "${url}", payload)\n  // add headers\n  res, _ := http.DefaultClient.Do(req)\n  defer res.Body.Close()\n  fmt.Println(res.Status)\n}`;
	}
	if (lang === 'php') {
		return `<?php\n$curl = curl_init();\ncurl_setopt_array($curl, [\n  CURLOPT_URL => "${url}",\n  CURLOPT_RETURNTRANSFER => true,\n  CURLOPT_CUSTOMREQUEST => "${method}",${bodyStr ? `\n  CURLOPT_POSTFIELDS => '${bodyStr}',` : ''}\n]);\n$response = curl_exec($curl);\ncurl_close($curl);\necho $response;`;
	}
	if (lang === 'http') {
		return `${method} ${url} HTTP/1.1\n${headerStr}${bodyStr ? '\n\n'+bodyStr : ''}`;
	}
	return JSON.stringify(raw, null, 2);
};

const toolboxDialogVisible = ref(false);
const paramsDepDialogVisible = ref(false);
const directDbDialogVisible = ref(false);
const publicFuncDialogVisible = ref(false);
const errorCodeDialogVisible = ref(false);
const envManageDialogVisible = ref(false);

// 顶部大 Tab
const mainTab = ref(props.initialTab || 'debug');
// 嵌入模式下，父组件切换 Tab 时同步
watch(() => props.initialTab, (v) => { if (v && props.embedded) mainTab.value = v; });

// 保存为用例弹窗
const saveCaseDialogVisible = ref(false);
const saveCaseLoading = ref(false);
const saveCaseSubmitting = ref(false);
const saveCaseSuiteTree = ref<any[]>([]);
const saveCaseForm = ref<{ name: string; description: string; suite_id: number | null; case_type: number }>({
	name: '', description: '', suite_id: null, case_type: 1,
});
const caseTypeOptions = [
	{ label: '正向', value: 1 }, { label: '负向', value: 2 },
	{ label: '边界值', value: 3 }, { label: '安全性', value: 4 }, { label: '其他', value: 5 },
];

const debugRecordList = ref<any[]>([]);
const apiDocInfo = ref<any>({});

// 解析接口文档（Swagger/OpenAPI/Apifox document 字段）
const docInfo = computed(() => {
	const info = props.apiData?.api_info || props.apiData || {};
	const doc = info.document;
	if (!doc) return null;

	const methodNames: Record<number,string> = { 1:'GET', 2:'POST', 3:'PUT', 4:'DELETE', 5:'PATCH', 6:'OPTIONS' };
	const methodName = methodNames[info.req?.method ?? 2] || 'GET';

	// parameters
	const parameters: any[] = Array.isArray(doc.parameters) ? doc.parameters : [];

	// requestBody
	let requestBody = null;
	let requestBodyType = '';
	let requestBodyFields: any[] = [];
	let requestBodyRaw = '';
	if (doc.requestBody) {
		const content = doc.requestBody.content || {};
		const ct = Object.keys(content)[0] || 'application/json';
		requestBodyType = ct;
		const schema = content[ct]?.schema || {};
		if (schema.properties) {
			const required = schema.required || [];
			requestBodyFields = Object.entries(schema.properties).map(([k, v]: any) => ({
				name: k, type: v.type || v.$ref?.split('/').pop() || '-',
				required: required.includes(k), description: v.description || ''
			}));
		} else {
			requestBodyRaw = JSON.stringify(schema, null, 2);
		}
		requestBody = doc.requestBody;
	}

	// responses
	const responses: any[] = [];
	if (doc.responses) {
		for (const [code, resp] of Object.entries(doc.responses as Record<string, any>)) {
			const content = resp.content || {};
			const ct = Object.keys(content)[0] || '';
			const schema = ct ? (content[ct]?.schema || {}) : {};
			let fields: any[] = [];
			let example = '';
			if (schema.properties) {
				fields = Object.entries(schema.properties).map(([k, v]: any) => ({
					name: k, type: v.type || '-', description: v.description || ''
				}));
			} else if (schema.items?.properties) {
				fields = Object.entries(schema.items.properties).map(([k, v]: any) => ({
					name: k, type: v.type || '-', description: v.description || ''
				}));
			} else if (Object.keys(schema).length) {
				example = JSON.stringify(schema, null, 2);
			}
			responses.push({ code: Number(code), description: resp.description || '', fields, example });
		}
	}

	return {
		name: info.name || doc.summary || doc.operationId || '接口文档',
		url: info.url || '',
		methodName,
		description: doc.description || doc.summary || '',
		parameters,
		requestBody,
		requestBodyType,
		requestBodyFields,
		requestBodyRaw,
		responses,
	};
});

// Mock
const mockBaseUrl = ref(window.location.origin);
const mockExpects = ref<any[]>([]);
const mockScriptEnabled = ref(false);
const mockScript = ref('');
const mockExpectDialogVisible = ref(false);
const newMockExpect = ref({ name: '', condition: '', body: '{"code":200,"data":{}}', status: 200 });
const copyMockUrl = () => {
	const url = `${mockBaseUrl.value}/mock${req.value.url || '/api/path'}`;
	navigator.clipboard?.writeText(url).then(() => ElMessage.success('已复制'));
};
const addMockExpect = () => {
	newMockExpect.value = { name: '', condition: '', body: '{"code":200,"data":{}}', status: 200 };
	mockExpectDialogVisible.value = true;
};
const confirmAddMockExpect = () => {
	if (!newMockExpect.value.name) { ElMessage.warning('请填写期望名称'); return; }
	mockExpects.value.push({ ...newMockExpect.value });
	mockExpectDialogVisible.value = false;
};

// 调试记录
const loadDebugHistory = async () => {
	try {
		const r: any = await req_history({});
		debugRecordList.value = Array.isArray(r?.data) ? r.data : [];
	} catch { debugRecordList.value = []; }
};
watch(mainTab, (v) => { if (v === 'history') loadDebugHistory(); });
const functionList = ref<any[]>([]);

// 证书管理
const certDialogVisible = ref(false);
const certPage = ref<'list'|'add'>('list');
const caEnabled = ref(false);
const caFileName = ref('');
const clientCerts = ref<any[]>([]);
const newCert = ref({ host: '', port: '443', crt: '', key: '', pfx: '', passphrase: '' });
const onCaFileChange = (file: any) => { caFileName.value = file.name; };
const addClientCert = () => {
	if (!newCert.value.host) { ElMessage.warning('请填写域名'); return; }
	clientCerts.value.push({ ...newCert.value });
	newCert.value = { host: '', port: '443', crt: '', key: '', pfx: '', passphrase: '' };
	certPage.value = 'list';
};

const loadFunctionList = async () => {
	try {
		const res: any = await apiAutomationApi.api_function_list({});
		const raw = res?.data;
		functionList.value = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	} catch { functionList.value = []; }
};

const req = ref({
	method: 1, url: '', params: [], header: [], body: '', body_type: 2,
	form_data: [], form_urlencoded: [], file_path: [], params_id: null,
	before: [], after: [], assert: [],
	config: { retry: 0, req_timeout: 30, res_timeout: 30, ssl_verify: true, allow_redirects: true, url_encode: false },
	xml_body: '', text_body: '', graphql_query: '', graphql_variables: '',
	cookies: [] as any[],
	auth_type: 'none', auth_token: '', auth_username: '', auth_password: '',
	auth_key: '', auth_value: '', auth_in: 'header',
});

const bodyTypes = [
	{ label: 'none', value: 1 }, { label: 'form-data', value: 3 },
	{ label: 'x-www-form-urlencoded', value: 4 }, { label: 'JSON', value: 2 },
	{ label: 'XML', value: 6 }, { label: 'Text', value: 7 },
	{ label: 'Binary', value: 5 }, { label: 'GraphQL', value: 8 },
];

const res = ref({ body: {}, header: {}, before: [], after: [], assert: [], code: 0, size: 0, res_time: 0, cookies: [], console: [], raw_request: null });

const method_list = ref([
	{ name: 'GET', value: 1, color: '#67C23A' }, { name: 'POST', value: 2, color: '#409EFF' },
	{ name: 'PUT', value: 3, color: '#E6A23C' }, { name: 'DELETE', value: 4, color: '#F56C6C' },
	{ name: 'PATCH', value: 5, color: '#8E44AD' }, { name: 'OPTIONS', value: 6, color: '#909399' },
]);

const val_type_list = ref([{ name: '环境变量', value: 1 }, { name: '全局变量', value: 2 }]);
const res_type_list = ref([
	{ name: '响应结果-JSON', value: 1 }, { name: '请求-Headers', value: 2 },
	{ name: '请求-Body', value: 3 }, { name: 'Headers-响应结果', value: 4 }, { name: '自定义目标', value: 5 }
]);

const tips = ref<any>('路径示例，结果{"code":200,"info":{"username":"admin"},"list":[{"id":1},{"id":2}]}\n例子：code=$.code, username=$.info.username，数组：$.list[0].id / $.list[1].id分别等于1 / 2');

const viewportH = ref(typeof window !== 'undefined' ? window.innerHeight : 900);
const onResize = () => { viewportH.value = window.innerHeight; };
onMounted(() => { window.addEventListener('resize', onResize); loadFunctionList(); });
onBeforeUnmount(() => window.removeEventListener('resize', onResize));

const resJsonHeight = computed(() => Math.max(120, Math.floor(viewportH.value * 0.28)));

const currentMethodColor = computed(() => {
	const m = method_list.value.find(m => m.value === req.value.method);
	return m?.color || '#409EFF';
});

const apiId = computed(() => {
	const d = props.apiData;
	return d?.api_id ?? d?.api_info?.id ?? d?.id ?? null;
});

const lastApiId = ref<number | string | null>(null);
watch(
	() => apiId.value,
	() => {
		const newId = apiId.value;
		if (newId == null) return;
		if (lastApiId.value === newId) return;
		lastApiId.value = newId;
		const apiInfo = props.apiData?.api_info || props.apiData || {};
		const reqSrc = apiInfo.req || {};
		const resSrc = apiInfo.res || {};
		req.value = {
			method: reqSrc.method ?? 2, url: reqSrc.url ?? apiInfo.url ?? '',
			params: Array.isArray(reqSrc.params) ? reqSrc.params : [],
			header: Array.isArray(reqSrc.header) ? reqSrc.header : [],
			body: typeof reqSrc.body === 'string' ? reqSrc.body : JSON.stringify(reqSrc.body != null ? reqSrc.body : {}, null, 2),
			body_type: reqSrc.body_type ?? 2,
			form_data: Array.isArray(reqSrc.form_data) ? reqSrc.form_data : [],
			form_urlencoded: Array.isArray(reqSrc.form_urlencoded) ? reqSrc.form_urlencoded : [],
			file_path: Array.isArray(reqSrc.file_path) ? reqSrc.file_path : [],
			params_id: reqSrc.params_id ?? apiInfo.params_id ?? null,
			before: Array.isArray(reqSrc.before) ? reqSrc.before : [],
			after: Array.isArray(reqSrc.after) ? reqSrc.after : [],
			assert: Array.isArray(reqSrc.assert) ? reqSrc.assert : [],
			config: { retry: reqSrc.config?.retry ?? 0, req_timeout: reqSrc.config?.req_timeout ?? 30, res_timeout: reqSrc.config?.res_timeout ?? 30, ssl_verify: reqSrc.config?.ssl_verify ?? true, allow_redirects: reqSrc.config?.allow_redirects ?? true, url_encode: reqSrc.config?.url_encode ?? false },
			xml_body: reqSrc.xml_body ?? '', text_body: reqSrc.text_body ?? '',
			graphql_query: reqSrc.graphql_query ?? '', graphql_variables: reqSrc.graphql_variables ?? '',
			cookies: Array.isArray(reqSrc.cookies) ? reqSrc.cookies : [],
			auth_type: reqSrc.auth_type ?? 'none', auth_token: reqSrc.auth_token ?? '',
			auth_username: reqSrc.auth_username ?? '', auth_password: reqSrc.auth_password ?? '',
			auth_key: reqSrc.auth_key ?? '', auth_value: reqSrc.auth_value ?? '', auth_in: reqSrc.auth_in ?? 'header',
		};
		res.value = { body: resSrc.body ?? {}, header: resSrc.header ?? {}, before: Array.isArray(resSrc.before) ? resSrc.before : [], after: Array.isArray(resSrc.after) ? resSrc.after : [], assert: Array.isArray(resSrc.assert) ? resSrc.assert : [], code: resSrc.code ?? 0, size: resSrc.size ?? 0, res_time: resSrc.res_time ?? 0, cookies: Array.isArray(resSrc.cookies) ? resSrc.cookies : [], console: Array.isArray(resSrc.console) ? resSrc.console : [], raw_request: resSrc.raw_request ?? null };
	},
	{ immediate: true }
);

const addParam = () => { req.value.params.push({ key: '', value: '', status: true }); };
const removeParam = (i: number) => { req.value.params.splice(i, 1); };
const addHeader = () => { req.value.header.push({ key: '', value: '', status: true }); };
const removeHeader = (i: number) => { req.value.header.splice(i, 1); };
const addFormData = () => { req.value.form_data.push({ key: '', value: '', status: true }); };
const removeFormData = (i: number) => { req.value.form_data.splice(i, 1); };
const addFormUrlencoded = () => { req.value.form_urlencoded.push({ key: '', value: '', status: true }); };
const removeFormUrlencoded = (i: number) => { req.value.form_urlencoded.splice(i, 1); };
const addCookie = () => { if (!req.value.cookies) req.value.cookies = []; req.value.cookies.push({ status: true, name: '', value: '', domain: '' }); };
const removeCookie = (i: number) => { req.value.cookies?.splice(i, 1); };

const addBefore = (type: number) => {
	const item: any = { type };
	if (type===1) { item.title=''; item.env_id=null; item.api_id=[]; }
	else if (type===2) { item.name=''; item.value=''; item.env_type=1; }
	else if (type===3) { item.wait_time=1; }
	else if (type===4) { item.title=''; item.code=''; }
	else if (type===5) { item.title=''; item.db_id=null; item.db_name=''; item.sql=''; item.result_var=''; }
	else if (type===6) { item.func_id=null; item.func_name=''; item.func_params=''; item.result_var=''; }
	req.value.before.push(item);
};
const removeBefore = (i: number) => { req.value.before.splice(i, 1); };

const addAfter = (type: number) => {
	const item: any = { type };
	if (type===1) { item.name=''; item.value=''; item.res_type=1; item.env_type=1; }
	else if (type===2) { item.wait_time=1; }
	else if (type===3) { item.assert_name=''; item.assert_path=''; item.assert_value=''; item.res_type=1; }
	else if (type===4) { item.title=''; item.db_id=null; item.db_name=''; item.sql=''; item.result_var=''; }
	else if (type===5) { item.code=''; }
	else if (type===6) { item.func_id=null; item.func_name=''; item.func_params=''; item.result_var=''; }
	else if (type===7) { item.import_title=''; item.env_id=null; item.api_id=[]; }
	req.value.after.push(item);
};
const removeAfter = (i: number) => { req.value.after.splice(i, 1); };

const addAssert = (type: number) => {
	const item: any = { type };
	if (type===1) { item.name=''; item.value=''; item.res_type=1; }
	else if (type===2) { item.ops_db=null; item.ops_db_table=''; item.ops_db_where=''; item.ops_db_assert=[]; }
	else if (type===3) { item.ops_redis=null; item.ops_redis_key=''; item.ops_redis_assert=[]; }
	else if (type===4) { item.local_db=null; item.local_db_table=''; item.local_db_where=''; item.local_db_assert=[]; }
	else if (type===5) { item.custom_name=''; item.custom_script=''; item.custom_expect=''; }
	req.value.assert.push(item);
};
const removeAssert = (i: number) => { req.value.assert.splice(i, 1); };

const uploadBinaryFile = async (options: any) => {
	try {
		const formData = new FormData();
		formData.append('file', options.file);
		const res: any = await fileApi.uploadFile(formData);
		if (res?.data?.url) { req.value.file_path.push(res.data.url); ElMessage.success('上传成功'); }
	} catch { ElMessage.error('上传失败'); }
};

const sendRequest = async () => {
	const id = apiId.value;
	if (!id) { ElMessage.warning('无法获取接口ID'); return; }
	try {
		const requestData: any = { id: Number(id), env_id: props.envId, url: req.value.url, req: req.value };
		const response: any = await api_send(requestData);
		if (response.code === 200) {
			const data = response.data;
			res.value = data?.res ? { ...res.value, ...data.res } : (data || res.value);
			ElMessage.success('请求发送成功');
		}
	} catch (error) {
		console.error('发送请求失败', error);
		ElMessage.error('请求发送失败');
	}
};

const handleSaveCommand = (command: string) => {
	if (command === 'save') saveApi();
	else if (command === 'saveAsCase') saveAsCase();
};

const saveApi = async () => {
	const id = apiId.value;
	if (!id) { ElMessage.warning('无法获取接口ID'); return; }
	try {
		await save_api({ id: Number(id), url: req.value.url, req: req.value });
		ElMessage.success('保存成功');
		emit('apiSaved');
	} catch { ElMessage.error('保存失败'); }
};

const saveAsCase = async () => {
	const apiServiceId = Number(props.serviceId ?? props.apiData?.api_info?.api_service_id ?? props.apiData?.api_service_id ?? 0);
	if (!apiServiceId) { ElMessage.warning('无法获取服务ID，请确认接口已关联服务'); return; }
	const defaultName = `${props.apiData?.name || props.apiData?.api_info?.name || '接口'}_用例_${Date.now()}`;
	saveCaseForm.value = { name: defaultName, description: '', suite_id: null, case_type: 1 };
	saveCaseSuiteTree.value = [];
	saveCaseLoading.value = true;
	saveCaseDialogVisible.value = true;
	try {
		const r: any = await apiAutomationApi.api_suite_list({ api_service_id: apiServiceId });
		const raw = r?.data;
		saveCaseSuiteTree.value = Array.isArray(raw) ? raw : (Array.isArray(raw?.content) ? raw.content : []);
	} catch (e) {
		console.error('加载用例集失败', e);
		saveCaseSuiteTree.value = [];
	} finally {
		saveCaseLoading.value = false;
	}
};

const reloadSuiteTree = async () => {
	const apiServiceId = Number(props.serviceId ?? props.apiData?.api_info?.api_service_id ?? props.apiData?.api_service_id ?? 0);
	if (!apiServiceId) return;
	saveCaseLoading.value = true;
	try {
		const r: any = await apiAutomationApi.api_suite_list({ api_service_id: apiServiceId });
		const raw = r?.data;
		saveCaseSuiteTree.value = Array.isArray(raw) ? raw : (Array.isArray(raw?.content) ? raw.content : []);
	} catch { saveCaseSuiteTree.value = []; }
	finally { saveCaseLoading.value = false; }
};

const confirmSaveAsCase = async () => {
	if (!saveCaseForm.value.name.trim()) { ElMessage.warning('请输入用例名称'); return; }
	if (!saveCaseForm.value.suite_id) { ElMessage.warning('请选择用例集'); return; }
	saveCaseSubmitting.value = true;
	try {
		await apiAutomationApi.save_api_case_to_suite({
			name: saveCaseForm.value.name.trim(),
			description: saveCaseForm.value.description,
			suite_id: saveCaseForm.value.suite_id,
			case_type: saveCaseForm.value.case_type,
			script: [{ api_id: apiId.value, name: props.apiData?.name || props.apiData?.api_info?.name || '接口', req: req.value }],
		});
		ElMessage.success('保存为用例成功');
		saveCaseDialogVisible.value = false;
		emit('caseSaved');
	} catch { ElMessage.error('保存失败'); }
	finally { saveCaseSubmitting.value = false; }
};
</script>

<style lang="scss" scoped>
.api-detail-container { height: calc(100vh - 100px); display: flex; flex-direction: column; padding: 0; margin: 0; overflow: hidden; background: var(--el-bg-color-page); }
.api-detail-container.is-embedded { height: 100%; flex: 1; min-height: 0; }
.api-detail-container.is-embedded .api-detail-card :deep(.el-card__body) { padding: 6px; }
.api-detail-card { height: 100%; flex: 1; display: flex; flex-direction: column; margin: 0; border: none; border-radius: 0; box-shadow: none; background: var(--el-bg-color-page); }
.api-detail-card :deep(.el-card__body) { height: 100%; display: flex; flex-direction: column; padding: 10px; background: var(--el-bg-color-page); box-sizing: border-box; }
.api-detail-content { flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 8px; }
.api-detail-header { flex: 0 0 auto; }
.req-url-bar { display: flex; align-items: center; gap: 6px; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; padding: 8px 12px; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.method-select { width: 110px; flex-shrink: 0; }
.method-select :deep(.el-input__inner) { color: var(--method-color, #409eff); font-weight: 700; font-size: 13px; }
.method-select :deep(.el-select__selected-item span) { color: var(--method-color, #409eff); font-weight: 700; font-size: 13px; }
.method-select :deep(.el-select__placeholder) { color: var(--method-color, #409eff); font-weight: 700; font-size: 13px; }
.url-input { flex: 1; min-width: 0; }
.url-input :deep(.el-input__inner) { font-family: 'Consolas', 'Monaco', monospace; font-size: 13px; }
.send-btn, .save-btn { flex-shrink: 0; }
.action-btn { flex-shrink: 0; color: var(--el-text-color-regular); border-color: var(--el-border-color); }
.action-btn:hover { color: #409eff; border-color: #409eff; }
.api-detail-body { flex: 1 1 auto; display: flex; flex-direction: column; gap: 8px; min-height: 0; }
.request-section { flex: 0 0 44%; min-height: 260px; }
.response-section { flex: 1 1 56%; min-height: 300px; display: flex; flex-direction: column; }
.panel-card { height: 100%; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.05); display: flex; flex-direction: column; overflow: hidden; }
.apifox-tabs { height: 100%; display: flex; flex-direction: column; }
.apifox-tabs :deep(.el-tabs__header) { margin: 0; background: var(--el-fill-color-light); border-bottom: 1px solid var(--el-border-color); padding: 0 8px; flex-shrink: 0; }
.apifox-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.apifox-tabs :deep(.el-tabs__item) { height: 38px; line-height: 38px; font-size: 12px; color: var(--el-text-color-regular); padding: 0 12px; transition: color .2s; letter-spacing: .2px; }
.apifox-tabs :deep(.el-tabs__item:hover) { color: #409eff; }
.apifox-tabs :deep(.el-tabs__item.is-active) { color: #1a6fe8; font-weight: 600; }
.apifox-tabs :deep(.el-tabs__active-bar) { height: 2px; background: linear-gradient(90deg,#409eff,#66b1ff); border-radius: 2px 2px 0 0; }
.apifox-tabs :deep(.el-tabs__content) { flex: 1; min-height: 0; overflow-y: auto; padding: 10px 12px; }
.apifox-tabs :deep(.el-tab-pane) { height: 100%; display: flex; flex-direction: column; min-height: 0; }
.apifox-tabs :deep(.el-badge__content) { top: 6px; right: 0px; font-size: 9px; height: 14px; line-height: 14px; padding: 0 3px; min-width: 14px; border: none; }
.res-badge :deep(.el-badge__content) { font-size: 9px; height: 13px; line-height: 13px; padding: 0 3px; min-width: 13px; border: none; }
.res-meta-tag { font-size: 11px; font-weight: 600; padding: 0 6px; height: 20px; line-height: 20px; border-radius: 3px; }
.res-tab-header { display: flex; align-items: center; background: var(--el-fill-color-light); border-bottom: 1px solid var(--el-border-color); flex-shrink: 0; min-height: 38px; }
.res-tabs { flex: 1; min-width: 0; }
.res-tabs :deep(.el-tabs__header) { background: transparent; border-bottom: none; margin: 0; }
.res-meta { display: flex; align-items: center; gap: 5px; padding: 0 12px; flex-shrink: 0; }
.res-meta-tag { font-size: 11px; font-weight: 600; padding: 0 6px; height: 20px; line-height: 20px; border-radius: 3px; }
.res-content { flex: 1; min-height: 0; overflow: hidden; display: flex; flex-direction: column; }
.json-panel { flex: 1; min-height: 0; height: 100%; overflow: auto; background: #fafbfc; padding: 4px; }
.res-code-panel { height: 100%; display: flex; flex-direction: column; background: #1e1e1e; border-radius: 0; overflow: hidden; }
.res-json-pretty { flex: 1; min-height: 0; }
.res-json-pretty :deep(.vjs-tree) { background: #1e1e1e !important; color: #d4d4d4 !important; font-family: 'Consolas','Monaco',monospace; font-size: 13px; padding: 12px; }
.res-json-pretty :deep(.vjs-key) { color: #9cdcfe !important; }
.res-json-pretty :deep(.vjs-value-string) { color: #ce9178 !important; }
.res-json-pretty :deep(.vjs-value-number) { color: #b5cea8 !important; }
.res-json-pretty :deep(.vjs-value-boolean) { color: #569cd6 !important; }
.res-json-pretty :deep(.vjs-value-null) { color: #569cd6 !important; }
.res-json-pretty :deep(.vjs-tree-node:hover) { background: transparent !important; }
.res-json-pretty :deep(.vjs-tree-node.is-highlight) { background: rgba(255,255,255,.06) !important; }
.res-json-pretty :deep(.vjs-tree-node-actions) { background: transparent !important; }
.res-json-pretty :deep(.vjs-tree-node:hover .vjs-tree-node-actions) { background: rgba(255,255,255,.06) !important; }
.res-console-panel { height: 100%; overflow-y: auto; background: #1e1e1e; padding: 8px 12px; font-family: 'Consolas','Monaco',monospace; font-size: 12px; }
.res-console-line { padding: 2px 0; line-height: 1.6; color: #d4d4d4; }
.console-error { color: #f48771; }
.console-warn { color: #dcdcaa; }
.console-info { color: #9cdcfe; }
.res-raw-panel { height: 100%; display: flex; flex-direction: column; background: #1e1e1e; overflow: hidden; }
.res-raw-toolbar { display: flex; align-items: center; gap: 2px; padding: 6px 12px; background: #252526; border-bottom: 1px solid #3c3c3c; flex-shrink: 0; flex-wrap: wrap; }
.raw-lang-item { padding: 3px 10px; border-radius: 3px; font-size: 12px; color: #cccccc; cursor: pointer; user-select: none; transition: all .15s; white-space: nowrap; }
.raw-lang-item:hover { color: #fff; background: #3c3c3c; }
.raw-lang-item.active { background: #0e639c; color: #fff; }
.res-raw-editor { flex: 1; min-height: 0; overflow: auto; padding: 12px; }
.res-raw-code { margin: 0; font-family: 'Consolas','Monaco',monospace; font-size: 12px; color: #d4d4d4; white-space: pre-wrap; word-break: break-all; line-height: 1.6; }
.res-empty { height: 100%; display: flex; align-items: center; justify-content: center; color: #909399; font-size: 13px; }
.op-pane { height: 100%; display: flex; flex-direction: column; min-height: 0; }
.op-scroll { flex: 1; min-height: 0; overflow-y: auto; padding: 4px 0; }
.op-footer { flex-shrink: 0; padding-top: 10px; background: var(--el-bg-color); position: sticky; bottom: 0; }
.body-pane { height: 100%; display: flex; flex-direction: column; min-height: 0; }
.body-type-bar { display: flex; align-items: center; gap: 2px; padding: 6px 0 8px; border-bottom: 1px solid var(--el-border-color-lighter); flex-shrink: 0; flex-wrap: wrap; }
.body-type-item { padding: 3px 10px; border-radius: 4px; font-size: 13px; color: var(--el-text-color-regular); cursor: pointer; user-select: none; transition: all .15s; white-space: nowrap; }
.body-type-item:hover { color: #409eff; background: var(--el-color-primary-light-9); }
.body-type-item.active { background: #409eff; color: #fff; font-weight: 500; }
.body-type-bar-right { margin-left: auto; }
.body-content { flex: 1; min-height: 0; overflow: auto; padding-top: 8px; }
.body-empty { height: 100%; display: flex; align-items: center; justify-content: center; color: var(--el-text-color-placeholder); font-size: 14px; }
.body-editor { height: 100%; }
.body-binary { padding: 8px 0; }
.body-kv { width: 100%; }
.kv-header { display: flex; align-items: center; padding: 4px 0; border-bottom: 1px solid var(--el-border-color-lighter); margin-bottom: 4px; font-size: 12px; color: var(--el-text-color-placeholder); }
.kv-row { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.kv-col-check { width: 24px; flex-shrink: 0; } .kv-col-key { flex: 1; } .kv-col-val { flex: 1; } .kv-col-act { width: 40px; flex-shrink: 0; }
.header-icon { margin-right: 6px; }
.tab-info { display: flex; align-items: center; gap: 4px; font-size: 13px; }
.code, .size { font-size: 13px; color: #409eff; margin-left: 4px; font-weight: 500; }

.res-dark-key { color: #9cdcfe; white-space: nowrap; }
.res-dark-val { color: #ce9178; word-break: break-all; }
.res-dark-empty { height: 100%; display: flex; align-items: center; justify-content: center; color: #555; font-size: 13px; background: #1e1e1e; font-family: 'Consolas','Monaco',monospace; }
.res-ops-title { display: flex; align-items: flex-start; gap: 8px; padding: 7px 16px; line-height: 1.5; }
.ops-fail { color: #f48771; }
.ops-icon { flex-shrink: 0; font-weight: 700; }
.res-ops-body { padding: 0 16px 8px; background: #252526; }

.res-dark-kv-panel { height: 100%; overflow-y: auto; background: #1e1e1e; }
.res-dark-kv-table { width: 100%; border-collapse: collapse; font-size: 12px; font-family: 'Consolas','Monaco',monospace; }
.res-dark-kv-table thead tr { background: #252526; }
.res-dark-kv-table th { color: #858585; font-weight: 500; padding: 7px 16px; text-align: left; border-bottom: 1px solid #3c3c3c; white-space: nowrap; font-size: 11px; letter-spacing: .5px; text-transform: uppercase; }
.res-dark-kv-table td { padding: 5px 16px; border-bottom: 1px solid #2d2d2d; vertical-align: top; }
.res-dark-kv-table tr:hover td { background: #2a2d2e; }
.res-dark-key { color: #9cdcfe; white-space: nowrap; }
.res-dark-val { color: #ce9178; word-break: break-all; }
.res-dark-muted { color: #858585; }
.res-dark-empty { height: 100%; display: flex; align-items: center; justify-content: center; color: #555; font-size: 13px; background: #1e1e1e; font-family: 'Consolas','Monaco',monospace; }
.res-ops-panel { height: 100%; overflow-y: auto; background: #1e1e1e; padding: 8px 0; font-family: 'Consolas','Monaco',monospace; font-size: 12px; }
.res-ops-item { border-bottom: 1px solid #2d2d2d; }
.res-ops-title { display: flex; align-items: flex-start; gap: 8px; padding: 7px 16px; line-height: 1.5; }
.ops-ok { color: #4ec9b0; }
.ops-fail { color: #f48771; }
.ops-icon { flex-shrink: 0; font-weight: 700; }
.res-ops-body { padding: 0 16px 8px; background: #252526; }
.code-editor-wrap { display: flex; flex-direction: column; background: #1e1e1e; border-radius: 6px; overflow: hidden; border: 1px solid #3c3c3c; flex: 1; }
.code-editor-lang { padding: 4px 12px; background: #252526; color: #858585; font-size: 11px; font-family: 'Consolas','Monaco',monospace; letter-spacing: .5px; border-bottom: 1px solid #3c3c3c; flex-shrink: 0; }
.code-textarea { flex: 1; width: 100%; min-height: 160px; background: #1e1e1e; color: #d4d4d4; border: none; outline: none; resize: vertical; padding: 12px; font-family: 'Consolas','Monaco',monospace; font-size: 13px; line-height: 1.6; tab-size: 2; box-sizing: border-box; }
.code-textarea::placeholder { color: #555; }
.code-textarea:focus { background: #1e1e1e; }
.json-editor-inner { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.json-editor-inner :deep(.jsoneditor-vue) { height: 100% !important; background: #1e1e1e; }
.json-editor-inner :deep(.jsoneditor) { border: none !important; background: #1e1e1e; }
.json-editor-inner :deep(.jsoneditor-menu) { background: #252526 !important; border-bottom: 1px solid #3c3c3c !important; }
.json-editor-inner :deep(.jsoneditor-menu button) { color: #ccc !important; }
.json-editor-inner :deep(.jsoneditor-tree) { background: #1e1e1e !important; color: #d4d4d4 !important; }
.json-editor-inner :deep(.jsoneditor-field) { color: #9cdcfe !important; }
.json-editor-inner :deep(.jsoneditor-value.jsoneditor-string) { color: #ce9178 !important; }
.json-editor-inner :deep(.jsoneditor-value.jsoneditor-number) { color: #b5cea8 !important; }
.json-editor-inner :deep(.jsoneditor-value.jsoneditor-boolean) { color: #569cd6 !important; }
.json-editor-inner :deep(.jsoneditor-value.jsoneditor-null) { color: #569cd6 !important; }
.json-editor-inner :deep(.ace_editor) { background: #1e1e1e !important; }
.json-editor-inner :deep(.ace_gutter) { background: #252526 !important; color: #858585 !important; }
.json-editor-inner :deep(.ace_content) { color: #d4d4d4 !important; }
.settings-pane { padding: 8px 4px; display: flex; flex-direction: column; gap: 0; }
.settings-item { display: flex; align-items: center; justify-content: space-between; padding: 14px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.settings-item:last-child { border-bottom: none; }
.settings-label { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--el-text-color-primary); }
.settings-help { font-size: 14px; color: var(--el-text-color-placeholder); cursor: help; }
.settings-help:hover { color: var(--el-text-color-regular); }
.cert-section { padding: 0; }
.cert-section-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
.cert-section-title { font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 3px; }
.cert-section-sub { font-size: 12px; color: var(--el-text-color-placeholder); }
.cert-field-row { display: flex; align-items: center; gap: 16px; margin-top: 8px; }
.cert-field-label { font-size: 13px; color: var(--el-text-color-regular); width: 70px; flex-shrink: 0; }
.cert-empty { font-size: 13px; color: var(--el-text-color-placeholder); padding: 12px 0; }
.cert-client-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: var(--el-fill-color-light); border-radius: 6px; margin-bottom: 6px; }
.cert-client-domain { font-size: 13px; color: var(--el-text-color-primary); font-family: monospace; margin-right: 8px; }
.cert-client-tag { display: inline-block; padding: 1px 6px; background: var(--el-color-primary-light-9); color: #409eff; border-radius: 3px; font-size: 11px; margin-right: 4px; }
.cert-breadcrumb { display: flex; align-items: center; margin-bottom: 4px; font-size: 13px; }
.main-tabs { flex-shrink: 0; }
.main-tabs :deep(.el-tabs__header) { margin: 0 0 8px; background: var(--el-bg-color); border-bottom: 2px solid var(--el-border-color); padding: 0 12px; }
.main-tabs :deep(.el-tabs__item) { height: 40px; line-height: 40px; font-size: 13px; color: var(--el-text-color-regular); padding: 0 16px; }
.main-tabs :deep(.el-tabs__item.is-active) { color: #409eff; font-weight: 600; }
.main-tabs :deep(.el-tabs__active-bar) { height: 2px; background: #409eff; }
.main-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
.side-panel { flex: 1; min-height: 0; overflow-y: auto; padding: 16px; background: var(--el-bg-color); border-radius: 8px; border: 1px solid var(--el-border-color); }
.side-panel-toolbar { margin-bottom: 12px; }
.side-panel-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--el-text-color-placeholder); font-size: 13px; gap: 8px; }
.history-list { display: flex; flex-direction: column; gap: 6px; }
.history-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: var(--el-fill-color-light); border-radius: 6px; }
.history-item-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.history-url { font-size: 12px; color: var(--el-text-color-regular); font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-time { font-size: 11px; color: var(--el-text-color-placeholder); flex-shrink: 0; margin-left: 8px; }
.mock-panel { }
.mock-section { }
.mock-section-title { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 10px; }
.mock-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.mock-addr-bar { display: flex; align-items: center; gap: 10px; background: var(--el-fill-color-light); border-radius: 6px; padding: 8px 12px; }
.mock-url { font-family: monospace; font-size: 12px; color: #409eff; flex: 1; word-break: break-all; }
.doc-panel { padding: 0; overflow-y: auto; }
.doc-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; background: var(--el-fill-color-light); border-bottom: 1px solid var(--el-border-color); flex-shrink: 0; }
.doc-header-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.doc-method-badge { display: inline-block; padding: 3px 10px; border-radius: 4px; color: #fff; font-size: 12px; font-weight: 700; letter-spacing: .5px; flex-shrink: 0; }
.doc-path { font-family: 'Consolas','Monaco',monospace; font-size: 14px; color: var(--el-text-color-primary); word-break: break-all; }
.doc-header-right { flex-shrink: 0; margin-left: 12px; }
.doc-desc-block { padding: 10px 20px; font-size: 13px; color: var(--el-text-color-regular); background: var(--el-color-warning-light-9); border-bottom: 1px solid var(--el-color-warning-light-5); line-height: 1.6; }
.doc-section { padding: 16px 20px; border-bottom: 1px solid var(--el-border-color-lighter); }
.doc-section:last-child { border-bottom: none; }
.doc-section-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #409eff; }
.doc-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.doc-table th { background: var(--el-fill-color-light); color: var(--el-text-color-placeholder); font-weight: 500; padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--el-border-color); white-space: nowrap; }
.doc-table td { padding: 8px 12px; border-bottom: 1px solid var(--el-border-color-lighter); vertical-align: top; color: var(--el-text-color-primary); }
.doc-table tr:last-child td { border-bottom: none; }
.doc-table tr:hover td { background: var(--el-fill-color-lighter); }
.doc-param-name { font-family: 'Consolas','Monaco',monospace; font-size: 12px; color: #e6a23c; font-weight: 600; }
.doc-type { font-family: 'Consolas','Monaco',monospace; font-size: 12px; color: #67c23a; }
.doc-optional { color: var(--el-text-color-placeholder); font-size: 12px; }
.doc-desc-cell { color: var(--el-text-color-regular); }
.doc-in-badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 500; }
.in-query { background: var(--el-color-primary-light-9); color: #409eff; }
.in-path { background: var(--el-color-warning-light-9); color: #e6a23c; }
.in-header { background: var(--el-color-success-light-9); color: #67c23a; }
.in-cookie { background: var(--el-color-danger-light-9); color: #f56c6c; }
.doc-content-type { font-size: 12px; color: var(--el-text-color-placeholder); margin-bottom: 10px; }
.doc-content-type code { background: var(--el-fill-color-light); padding: 1px 6px; border-radius: 3px; font-family: monospace; color: var(--el-text-color-regular); }
.doc-raw-schema { background: #1e1e1e; border-radius: 6px; overflow: hidden; margin-top: 8px; }
.doc-pre { margin: 0; padding: 12px 14px; font-family: 'Consolas','Monaco',monospace; font-size: 12px; color: #d4d4d4; white-space: pre-wrap; word-break: break-all; line-height: 1.6; }
.doc-response-item { margin-bottom: 12px; }
.doc-response-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.doc-response-desc { font-size: 13px; color: var(--el-text-color-regular); }
.res-code-toolbar { display: flex; justify-content: flex-end; padding: 5px 10px; background: #252526; border-bottom: 1px solid #3c3c3c; flex-shrink: 0; }
.res-copy-btn { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; background: transparent; border: 1px solid #4a4a4a; border-radius: 3px; color: #aaa; font-size: 11px; cursor: pointer; transition: all .15s; }
.res-copy-btn:hover { background: #3c3c3c; color: #e0e0e0; border-color: #666; }
.res-copy-btn.copied { color: #4ec9b0; border-color: #4ec9b0; }
</style>
