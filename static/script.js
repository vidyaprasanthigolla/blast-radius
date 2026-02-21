document.addEventListener('DOMContentLoaded', () => {
    const cyContainer = document.getElementById('cy');
    let cy = cytoscape({
        container: cyContainer,
        elements: [],
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'color': '#fff',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'font-size': '12px',
                    'font-family': 'Inter, sans-serif',
                    'background-color': '#2c303a',
                    'width': 24,
                    'height': 24
                }
            },
            {
                selector: 'node[?highlighted]',
                style: {
                    'background-color': '#ff7e67', // default highlight (adjust based on direct/indirect later)
                    'width': 30,
                    'height': 30,
                    'border-width': 2,
                    'border-color': '#fff'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#3a3f4c',
                    'target-arrow-color': '#3a3f4c',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '10px',
                    'color': '#888',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -8
                }
            }
        ],
        layout: {
            name: 'cose',
            padding: 30
        }
    });

    const analyzeBtn = document.getElementById('analyze-btn');
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error-message');
    
    // Stats
    const statTotal = document.getElementById('stat-total');
    const statDirect = document.getElementById('stat-direct');
    const statIndirect = document.getElementById('stat-indirect');
    
    const impactList = document.getElementById('impact-list');

    analyzeBtn.addEventListener('click', async () => {
        const path = document.getElementById('codebase-path').value.trim();
        const intent = document.getElementById('change-intent').value.trim();

        if (!path || !intent) {
            showError("Please provide both codebase path and change intent.");
            return;
        }

        hideError();
        setLoading(true);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    codebase_path: path,
                    change_intent: intent
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Analysis failed");
            }

            renderResults(data);

        } catch (err) {
            showError(err.message);
        } finally {
            setLoading(false);
        }
    });

    function renderResults(data) {
        // Update Graph
        cy.elements().remove();
        
        // Custom styling based on direct vs indirect
        const directIds = new Set(data.start_nodes);
        
        const enhancedElements = data.graph_data.map(el => {
            if (el.data.id && el.data.highlighted !== undefined) {
                // it's a node
                if (directIds.has(el.data.id)) {
                    el.classes = 'direct';
                } else if (el.data.highlighted) {
                    el.classes = 'indirect';
                }
            }
            return el;
        });

        cy.add(enhancedElements);
        
        cy.style()
            .selector('.direct')
            .style({
                'background-color': '#ff7e67', // node-direct
                'border-color': '#fff'
            })
            .selector('.indirect')
            .style({
                'background-color': '#f1c40f', // node-indirect
                'border-color': '#fff'
            })
            .update();

        cy.layout({ name: 'cose', padding: 50 }).run();

        // Update Stats
        const impacts = data.impacts || [];
        statTotal.textContent = impacts.length;
        statDirect.textContent = impacts.filter(i => i.is_direct).length;
        statIndirect.textContent = impacts.filter(i => !i.is_direct).length;

        // Update List
        impactList.innerHTML = '';
        if (impacts.length === 0) {
            impactList.innerHTML = '<p class="placeholder-text">No impacts detected.</p>';
            return;
        }

        // Sort: direct first
        impacts.sort((a, b) => (b.is_direct ? 1 : 0) - (a.is_direct ? 1 : 0));

        impacts.forEach(impact => {
            const item = document.createElement('div');
            item.className = 'impact-item';
            
            const directTagClass = impact.is_direct ? 'tag-direct' : 'tag-indirect';
            const directTagText = impact.is_direct ? 'Direct Impact' : 'Indirect Impact';

            item.innerHTML = `
                <div class="impact-header">
                    <span class="impact-title">${escapeHTML(impact.id)}</span>
                    <div class="impact-tags">
                        <span class="tag tag-category">${escapeHTML(impact.category)}</span>
                        <span class="tag ${directTagClass}">${directTagText}</span>
                    </div>
                </div>
                <div class="impact-explanation">
                    ${escapeHTML(impact.explanation)}
                </div>
            `;
            
            impactList.appendChild(item);
        });
    }

    function setLoading(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            loadingEl.classList.remove('hidden');
        } else {
            analyzeBtn.disabled = false;
            loadingEl.classList.add('hidden');
        }
    }

    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.classList.remove('hidden');
    }

    function hideError() {
        errorEl.classList.add('hidden');
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }
});
