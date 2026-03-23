// v-throttle
// 迁移自旧前端 l-vue-ui/src/directives/modules/throttle.ts
import type { Directive, DirectiveBinding } from 'vue';

interface ElType extends HTMLElement {
	handleClick?: () => any;
	disabled?: boolean;
}

export const throttleDirective: Directive = {
	mounted(el: ElType, binding: DirectiveBinding) {
		const delay = parseInt(binding.arg as any) || 500;
		const handler = binding.value;
		let lastExecTime = 0;
		el.addEventListener(
			'click',
			() => {
				const now = Date.now();
				if (now - lastExecTime > delay) {
					handler();
					lastExecTime = now;
				}
			},
			{ passive: false }
		);
	},
};

