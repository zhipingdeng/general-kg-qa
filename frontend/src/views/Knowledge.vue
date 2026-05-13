<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <Header />
    
    <div class="flex-1 overflow-hidden flex flex-col">
      <!-- Toolbar -->
      <div class="bg-white border-b border-gray-200 px-4 py-3">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <h2 class="text-lg font-semibold text-gray-900">知识图谱</h2>
            <span class="text-sm text-gray-500">
              {{ graphData.nodes.length }} 个实体，{{ graphData.edges.length }} 条关系
            </span>
          </div>
          <div class="flex items-center space-x-3">
            <button
              @click="refreshGraph"
              :disabled="loading"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              刷新
            </button>
            <button
              @click="resetZoom"
              class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              重置视图
            </button>
          </div>
        </div>
      </div>

      <!-- Graph Container -->
      <div class="flex-1 relative">
        <!-- Loading -->
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
          <div class="text-center">
            <svg class="animate-spin h-8 w-8 text-primary-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <p class="text-gray-600">加载知识图谱中...</p>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="graphData.nodes.length === 0" class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <p class="text-gray-500 mb-4">暂无知识图谱数据</p>
            <button
              @click="refreshGraph"
              class="btn-primary text-white px-6 py-2 rounded-lg"
            >
              加载数据
            </button>
          </div>
        </div>

        <!-- SVG Graph -->
        <svg
          ref="svgRef"
          class="w-full h-full"
          @mousedown="onMouseDown"
        />

        <!-- Tooltip -->
        <div
          v-if="tooltip.visible"
          class="absolute bg-white rounded-lg shadow-lg border border-gray-200 p-3 max-w-xs z-20 pointer-events-none"
          :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
        >
          <div class="font-semibold text-gray-900 mb-1">{{ tooltip.name }}</div>
          <div v-if="tooltip.tag" class="text-xs text-gray-500 mb-1">标签：{{ tooltip.tag }}</div>
          <div v-if="tooltip.desc" class="text-sm text-gray-600 line-clamp-3">{{ tooltip.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import { knowledgeApi } from '@/api/qa'
import type { KnowledgeNode, KnowledgeEdge, KnowledgeGraph } from '@/types'
import Header from '@/components/Header.vue'

const svgRef = ref<SVGSVGElement>()
const loading = ref(false)

const graphData = reactive<KnowledgeGraph>({
  nodes: [],
  edges: []
})

const tooltip = reactive({
  visible: false,
  x: 0,
  y: 0,
  name: '',
  tag: '',
  desc: ''
})

let simulation: d3.Simulation<KnowledgeNode, KnowledgeEdge> | null = null
let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
let g: d3.Selection<SVGGElement, unknown, null, undefined> | null = null
let zoom: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null

// Color scale for different tags
const colorScale = d3.scaleOrdinal(d3.schemeCategory10)

async function refreshGraph() {
  loading.value = true
  try {
    const data = await knowledgeApi.getGraph(100)
    graphData.nodes = data.nodes
    graphData.edges = data.edges
    renderGraph()
  } catch (e) {
    console.error('Failed to load knowledge graph:', e)
  } finally {
    loading.value = false
  }
}

function renderGraph() {
  if (!svgRef.value || graphData.nodes.length === 0) return

  // Clear previous
  d3.select(svgRef.value).selectAll('*').remove()

  const width = svgRef.value.clientWidth
  const height = svgRef.value.clientHeight

  svg = d3.select(svgRef.value)
  g = svg.append('g')

  // Zoom
  zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g!.attr('transform', event.transform)
    })

  svg.call(zoom)

  // Create node map for edges
  const nodeMap = new Map(graphData.nodes.map(n => [n.id, n]))

  // Filter edges to only include those with both nodes present
  const validEdges = graphData.edges.filter(e => nodeMap.has(e.source) && nodeMap.has(e.target))

  // Simulation
  simulation = d3.forceSimulation<KnowledgeNode>(graphData.nodes)
    .force('link', d3.forceLink<KnowledgeNode, KnowledgeEdge>(validEdges)
      .id(d => d.id)
      .distance(100)
    )
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(30))

  // Arrow markers
  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '-0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('orient', 'auto')
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .append('path')
    .attr('d', 'M 0,-5 L 10,0 L 0,5')
    .attr('fill', '#94a3b8')

  // Edges
  const edgeGroup = g.append('g').attr('class', 'edges')
  const edges = edgeGroup.selectAll('line')
    .data(validEdges)
    .enter()
    .append('line')
    .attr('stroke', '#94a3b8')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.6)
    .attr('marker-end', 'url(#arrowhead)')

  // Edge labels
  const edgeLabels = edgeGroup.selectAll('text')
    .data(validEdges)
    .enter()
    .append('text')
    .attr('font-size', '10px')
    .attr('fill', '#64748b')
    .attr('text-anchor', 'middle')
    .attr('dy', -5)
    .text(d => d.type)

  // Nodes
  const nodeGroup = g.append('g').attr('class', 'nodes')
  const nodes = nodeGroup.selectAll('g')
    .data(graphData.nodes)
    .enter()
    .append('g')
    .attr('class', 'kg-node')
    .call(d3.drag<SVGGElement, KnowledgeNode>()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded)
    )

  // Node circles
  nodes.append('circle')
    .attr('r', 12)
    .attr('fill', d => colorScale(d.tag || 'default'))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .on('mouseover', (event, d) => {
      tooltip.visible = true
      tooltip.name = d.name
      tooltip.tag = d.tag
      tooltip.desc = d.desc
      updateTooltipPosition(event)
    })
    .on('mousemove', (event) => {
      updateTooltipPosition(event)
    })
    .on('mouseout', () => {
      tooltip.visible = false
    })

  // Node labels
  nodes.append('text')
    .attr('dx', 15)
    .attr('dy', 4)
    .attr('font-size', '12px')
    .attr('fill', '#374151')
    .text(d => d.name.length > 10 ? d.name.slice(0, 10) + '...' : d.name)

  // Tick
  simulation.on('tick', () => {
    edges
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    edgeLabels
      .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
      .attr('y', (d: any) => (d.source.y + d.target.y) / 2)

    nodes.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })
}

function updateTooltipPosition(event: MouseEvent) {
  const container = svgRef.value?.parentElement
  if (!container) return
  const rect = container.getBoundingClientRect()
  tooltip.x = event.clientX - rect.left + 10
  tooltip.y = event.clientY - rect.top - 10
}

function dragStarted(event: d3.D3DragEvent<SVGGElement, KnowledgeNode, KnowledgeNode>, d: KnowledgeNode) {
  if (!event.active && simulation) simulation.alphaTarget(0.3).restart()
  ;(d as any).fx = (d as any).x
  ;(d as any).fy = (d as any).y
}

function dragged(event: d3.D3DragEvent<SVGGElement, KnowledgeNode, KnowledgeNode>, d: KnowledgeNode) {
  ;(d as any).fx = event.x
  ;(d as any).fy = event.y
}

function dragEnded(event: d3.D3DragEvent<SVGGElement, KnowledgeNode, KnowledgeNode>, d: KnowledgeNode) {
  if (!event.active && simulation) simulation.alphaTarget(0)
  ;(d as any).fx = null
  ;(d as any).fy = null
}

function resetZoom() {
  if (svg && zoom) {
    svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity)
  }
}

function onMouseDown() {
  tooltip.visible = false
}

onMounted(() => {
  // Auto-load on mount
  refreshGraph()
})

onUnmounted(() => {
  if (simulation) simulation.stop()
})
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
