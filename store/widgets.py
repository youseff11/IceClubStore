import json

from django import forms
from django.utils.html import escape
from django.utils.safestring import mark_safe


class SizeChartWidget(forms.Textarea):
    """
    جدول مقاسات قابل للتعديل (صفوف وأعمدة) بدل الـ textarea.
    القيمة بتتخزن نص عادي: أول سطر عناوين الأعمدة، وكل سطر بعده مقاس، والأعمدة مفصولة بفاصلة.
    """
    default_headers = ['Size', 'Height (cm)', 'Weight (kg)']

    def __init__(self, attrs=None, sizes=None, hint=""):
        super().__init__(attrs)
        self.sizes = sizes or []
        self.hint = hint

    def render(self, name, value, attrs=None, renderer=None):
        attrs = {**(attrs or {}), 'style': 'display:none'}
        textarea = super().render(name, value, attrs, renderer)
        root_id = f"scw-{attrs.get('id') or name}"
        hint = f'<p class="scw-hint">{escape(self.hint)}</p>' if self.hint else ''
        return mark_safe(
            f'<div class="scw" id="{escape(root_id)}" '
            f'data-default-headers="{escape(json.dumps(self.default_headers))}" '
            f'data-sizes="{escape(json.dumps(self.sizes))}">'
            f'{textarea}'
            '<div class="scw-scroll"><table class="scw-table"><thead></thead><tbody></tbody></table></div>'
            '<div class="scw-actions">'
            '<button type="button" class="scw-btn scw-add-row">+ Add Size</button>'
            '<button type="button" class="scw-btn scw-add-col">+ Add Column</button>'
            '<button type="button" class="scw-btn scw-clear">Clear Table</button>'
            '</div>'
            f'{hint}'
            '</div>'
            f'{WIDGET_ASSETS}'
            f'<script>initSizeChart(document.getElementById("{escape(root_id)}"));</script>'
        )


WIDGET_ASSETS = """
<style>
.scw { max-width: 760px; }
.scw-scroll { overflow-x: auto; }
.scw-table { border-collapse: collapse; width: 100%; }
.scw-table th, .scw-table td { padding: 4px; border: none; background: none; vertical-align: middle; }
.scw-table thead th { font-weight: 700; }
.scw-table input {
    width: 100%; min-width: 90px; box-sizing: border-box; padding: 7px 9px; border-radius: 6px; font-size: 13px;
    background: transparent; color: inherit; border: 1px solid var(--border-color, rgba(127,127,127,0.35));
}
.scw-table thead input { font-weight: 700; background: rgba(79,195,247,0.12); border-color: rgba(79,195,247,0.45); }
.scw-table input:focus { outline: none; border-color: #4fc3f7; box-shadow: 0 0 0 2px rgba(79,195,247,0.25); }
.scw-x {
    width: 26px; height: 26px; border-radius: 50%; border: 1px solid rgba(255,82,82,0.5); background: transparent;
    color: #ff5252; cursor: pointer; font-size: 13px; line-height: 1; padding: 0;
}
.scw-x:hover { background: #ff5252; color: #fff; }
.scw-head-cell { display: flex; gap: 4px; align-items: center; }
.scw-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.scw-btn {
    padding: 7px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600;
    border: 1px solid #4fc3f7; background: rgba(79,195,247,0.1); color: #4fc3f7;
}
.scw-btn:hover { background: #4fc3f7; color: #0f2027; }
.scw-clear { border-color: rgba(127,127,127,0.5); background: transparent; color: inherit; opacity: 0.8; }
.scw-clear:hover { background: rgba(255,82,82,0.15); color: #ff5252; border-color: #ff5252; }
.scw-hint { margin: 8px 0 0; font-size: 12px; opacity: 0.65; }
</style>
<script>
if (!window.initSizeChart) {
    window.initSizeChart = function (root) {
        const ta = root.querySelector('textarea');
        const thead = root.querySelector('thead');
        const tbody = root.querySelector('tbody');
        const clean = v => String(v || '').replace(/[,|\\t\\r\\n]+/g, ' ').replace(/\\s+/g, ' ').trim();

        let lines = (ta.value || '').split(/\\r?\\n/).map(l => l.trim()).filter(Boolean)
            .map(l => l.split(/[,\\t|]/).map(c => c.trim()));
        let headers = lines[0] || [];
        let rows = lines.slice(1);

        function freshTable() {
            headers = JSON.parse(root.dataset.defaultHeaders);
            const sizes = JSON.parse(root.dataset.sizes || '[]');
            rows = (sizes.length ? sizes : ['']).map(s => [s].concat(Array(headers.length - 1).fill('')));
        }
        if (!headers.length) freshTable();
        rows = rows.map(r => headers.map((_, i) => r[i] || ''));

        // يحدّث الـ textarea المخفية؛ ولو مفيش أي قيم غير أسماء المقاسات بيسيبها فاضية (يتبع جايد القسم)
        function sync() {
            const hasData = rows.some(r => r.slice(1).some(c => clean(c)));
            if (!hasData) { ta.value = ''; return; }
            const out = [headers.map(clean).join(', ')];
            rows.forEach(r => { if (r.some(c => clean(c))) out.push(r.map(clean).join(', ')); });
            ta.value = out.join('\\n');
        }

        function input(value, onInput, placeholder) {
            const el = document.createElement('input');
            el.type = 'text';
            el.value = value;
            el.placeholder = placeholder || '';
            el.addEventListener('input', () => { onInput(el.value); sync(); });
            return el;
        }

        function removeBtn(title, onClick) {
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'scw-x';
            b.title = title;
            b.textContent = '✕';
            b.addEventListener('click', () => { onClick(); render(); sync(); });
            return b;
        }

        function render() {
            thead.innerHTML = '';
            tbody.innerHTML = '';
            const hr = document.createElement('tr');
            headers.forEach((h, ci) => {
                const th = document.createElement('th');
                const cell = document.createElement('div');
                cell.className = 'scw-head-cell';
                cell.appendChild(input(h, v => { headers[ci] = v; }, 'Column name'));
                if (ci > 0) cell.appendChild(removeBtn('Remove column', () => {
                    headers.splice(ci, 1);
                    rows.forEach(r => r.splice(ci, 1));
                }));
                th.appendChild(cell);
                hr.appendChild(th);
            });
            hr.appendChild(document.createElement('th'));
            thead.appendChild(hr);

            rows.forEach((r, ri) => {
                const tr = document.createElement('tr');
                r.forEach((c, ci) => {
                    const td = document.createElement('td');
                    td.appendChild(input(c, v => { rows[ri][ci] = v; }, ci === 0 ? 'e.g. M' : ''));
                    tr.appendChild(td);
                });
                const td = document.createElement('td');
                td.appendChild(removeBtn('Remove size', () => { rows.splice(ri, 1); }));
                tr.appendChild(td);
                tbody.appendChild(tr);
            });
        }

        root.querySelector('.scw-add-row').addEventListener('click', () => {
            rows.push(Array(headers.length).fill(''));
            render();
            tbody.lastElementChild.querySelector('input').focus();
        });
        root.querySelector('.scw-add-col').addEventListener('click', () => {
            headers.push('');
            rows.forEach(r => r.push(''));
            render();
            thead.querySelectorAll('input')[headers.length - 1].focus();
        });
        root.querySelector('.scw-clear').addEventListener('click', () => {
            if (!confirm('Clear the whole table?')) return;
            freshTable();
            rows = rows.map(r => r.map((c, i) => (i === 0 ? c : '')));
            render();
            sync();
        });

        render();
        sync();
    };
}
</script>
"""
