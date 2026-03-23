/**
 * mitmproxy 抓包模块接口
 * 对应后端 /api/v1/mitmproxy/*
 */
import request from '/@/utils/request';

export const mitmproxy_start = (data: any) => {
  return request.post('/v1/mitmproxy/mitmproxy_start', data);
};

export const mitmproxy_single_start = (data: any) => {
  return request.post('/v1/mitmproxy/mitmproxy_single_start', data);
};

export const mitmproxy_check = (data: any) => {
  return request.post('/v1/mitmproxy/mitmproxy_check', data);
};

export const mitmproxy_stop = (data: any) => {
  return request.post('/v1/mitmproxy/mitmproxy_stop', data);
};

export const mitmproxy_close_agent = (data: any) => {
  return request.post('/v1/mitmproxy/mitmproxy_close_agent', data);
};

export const mitmproxy_run_log = (data: any) => {
  return request.post('/v1/mitmproxy/mitmproxy_run_log', data);
};

export const mitmproxy_write_api = (data: any) => {
  return request.post('/v1/mitmproxy/mitmproxy_write_api', data);
};

export const single_write = (data: any) => {
  return request.post('/v1/mitmproxy/single_write', data);
};

