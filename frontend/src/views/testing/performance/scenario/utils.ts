/**
 * 压测场景 — 纯函数共享层
 * 供 index.vue（子列表操作）与 addUpdate.vue（表单提交）共同使用
 */

export const THREAD_TYPE_LABELS: Record<string, string> = {
	'0': 'SetUp',
	'1': 'Standard',
	'2': 'Stepping',
	'3': 'Ultimate',
};

/** ultimate_rows 防御式解析：兼容 array / JSON string / null */
export function normalizeUltimateRows(raw: any): any[] {
	if (!raw) return [];
	if (Array.isArray(raw)) return raw;
	if (typeof raw === 'string') {
		try {
			const parsed = JSON.parse(raw);
			return Array.isArray(parsed) ? parsed : [];
		} catch {
			return [];
		}
	}
	return [];
}

/** 后端子配置字段 → 前端字段，同时计算 known_times / has_unknown_times */
export function normalizeConfig(raw: any): any {
	const tt: string = raw.thread_type ?? '1';
	const forever = raw.loop_forever === 1;
	const dur = raw.duration ?? 0;
	const ramp = raw.ramp_up_time ?? 0;
	const delay = raw.startup_delay ?? 0;

	let known_times = 0;
	let has_unknown_times = false;
	if (raw.estimated_duration != null) {
		known_times = raw.estimated_duration;
	} else if (['0', '1'].includes(tt)) {
		known_times = ramp + delay;
		if (forever && dur > 0) { known_times += dur; }
		else { has_unknown_times = true; }
	} else if (tt === '2') {
		const maxT  = raw.thread_count || 0;
		const burst = raw.step_start_users_burst || 0;
		const count = raw.step_start_users_count || 0;
		const period = raw.step_start_users_period || 0;
		const rampUp = raw.step_ramp_up || 0;
		const sCnt  = raw.step_stop_users_count || 0;
		const sPer  = raw.step_stop_users_period || 0;
		const stepsUp   = count > 0 && maxT > burst ? Math.ceil((maxT - burst) / count) : 0;
		const stepsDown = sCnt > 0 && maxT > 0 ? Math.ceil(maxT / sCnt) : 0;
		// period 是每批爬坡完成后的等待间隔，每批（含初始burst）各自占用 rampUp 秒
		known_times = (raw.step_initial_delay || 0) + (stepsUp + 1) * rampUp + stepsUp * period + (raw.step_flight_time || 0) + stepsDown * sPer;
	} else if (tt === '3') {
		const rows = Array.isArray(raw.ultimate_rows) ? raw.ultimate_rows : [];
		if (rows.length > 0) {
			const times = rows.map((r: any) => (r.initial_delay || 0) + (r.startup_time || 0) + (r.hold_load_for || 0) + (r.shutdown_time || 0));
			known_times = Math.max(...times);
		}
	}

	return {
		id: raw.id,
		tg_name: raw.tg_name ?? '',
		thread_type: tt,
		thread_type_label: THREAD_TYPE_LABELS[tt] ?? tt,
		active: tt === '3' ? true : raw.status === 1,
		threads: raw.thread_count,
		ramp_up: raw.ramp_up_time,
		loop_count: raw.loop_count,
		forever,
		duration: raw.duration,
		start_delay: raw.startup_delay,
		step_initial_delay:      raw.step_initial_delay,
		step_start_users_count:  raw.step_start_users_count,
		step_start_users_burst:  raw.step_start_users_burst,
		step_start_users_period: raw.step_start_users_period,
		step_stop_users_count:   raw.step_stop_users_count,
		step_stop_users_period:  raw.step_stop_users_period,
		step_flight_time:        raw.step_flight_time,
		step_ramp_up:            raw.step_ramp_up,
		ultimate_rows: normalizeUltimateRows(raw.ultimate_rows),
		estimated_duration: raw.estimated_duration ?? null,
		known_times,
		has_unknown_times,
	};
}

/** 前端表单子配置 → 后端请求体（兼容 standard / stepping / ultimate 三种类型） */
export function buildConfigPayload(cfg: any, withStatus?: number): any {
	const tt: string = cfg.thread_type ?? '1';
	const payload: any = {
		thread_type: tt,
	};
	if (cfg.tg_name)              payload.tg_name    = cfg.tg_name;
	if (withStatus !== undefined) payload.status     = withStatus;

	if (tt === '0' || tt === '1') {
		payload.thread_count  = cfg.threads;
		payload.ramp_up_time  = cfg.ramp_up;
		payload.loop_forever  = cfg.forever ? 1 : 0;
		payload.startup_delay = cfg.start_delay ?? 0;
		if (!cfg.forever && cfg.loop_count !== undefined) payload.loop_count = cfg.loop_count;
		if (cfg.forever  && cfg.duration  !== undefined) payload.duration   = cfg.duration;
	} else if (tt === '2') {
		payload.thread_count              = cfg.threads;
		payload.step_initial_delay        = cfg.step_initial_delay      ?? 0;
		payload.step_start_users_count    = cfg.step_start_users_count;
		payload.step_start_users_burst    = cfg.step_start_users_burst  ?? 0;
		payload.step_start_users_period   = cfg.step_start_users_period;
		payload.step_stop_users_count     = cfg.step_stop_users_count   ?? 0;
		payload.step_stop_users_period    = cfg.step_stop_users_period  ?? 0;
		payload.step_flight_time          = cfg.step_flight_time        ?? 0;
		payload.step_ramp_up              = cfg.step_ramp_up            ?? 0;
	} else if (tt === '3') {
		payload.ultimate_rows = (cfg.ultimate_rows ?? []).map((r: any) => ({
			start_threads: r.start_threads ?? 0,
			initial_delay: r.initial_delay ?? 0,
			startup_time:  r.startup_time  ?? 0,
			hold_load_for: r.hold_load_for ?? 0,
			shutdown_time: r.shutdown_time ?? 0,
		}));
	}
	if (cfg.estimated_duration != null) payload.estimated_duration = cfg.estimated_duration;
	return payload;
}