export type ProjectStatus =
  | 'DRAFT'
  | 'READY_FOR_COLLECTION'
  | 'COLLECTING'
  | 'COLLECTED'
  | 'READY_FOR_REVIEW'
  | 'APPROVED_FOR_ANALYSIS'
  | 'ANALYZING'
  | 'ANALYZED'
  | 'READY_FOR_FINAL_REVIEW'
  | 'APPROVED'
  | 'FAILED'

export interface Project {
  id: string
  name: string
  brand_name: string
  market: string
  product_or_service: string
  target_buying_decision: string
  purchase_type: string
  primary_segment: string
  primary_bottleneck: string
  status: ProjectStatus
}

export type Bottleneck = 'unknown' | 'attention' | 'desire' | 'persuasion' | 'friction'

export interface SetupStatus {
  status: ProjectStatus
  missing_fields: string[]
  ready_for_collection: boolean
  bottleneck_resolved: boolean
  conditional: boolean
  can_submit_setup: boolean
  allowed_transitions: ProjectStatus[]
}

export interface Entity {
  id: string
  project_id: string
  name: string
  entity_type: 'brand' | 'competitor'
  comparable_status: string
}

export interface Source {
  id: string
  entity_id: string
  source_type: string
  url: string
  status: string
  accessible_count: number
  failed_count: number
}

export type ReviewStatus =
  | 'pending_review'
  | 'approved'
  | 'edited_and_approved'
  | 'rejected'
  | 'hypothesis'
  | 'conflict'

export interface Evidence {
  id: string
  entity_id: string
  content_item_id: string
  verbatim_text: string
  normalized_summary: string
  finding_status: string
  category: string
  confidence: string
  review_status: ReviewStatus
  reviewer: string | null
  reviewed_at: string | null
  review_note: string
}

export interface ReviewDecision {
  status: ReviewStatus
  edited_value?: string
  reviewer: string
  note?: string
}

export interface SalesElement {
  id: string
  canonical_element_id: string
  canonical_key: string
  presence_status: string
  computed_score: number | null
  confidence: string
  recommendation: string
  review_status: string
  evidence_ids: string[]
}

export interface Gap {
  id: string
  title: string
  gap_type: string
  status: string
  severity: string
  confidence: string
  root_cause: string
  review_status: string
}

export interface Dashboard {
  project: Project
  entities: Entity[]
  sources: Source[]
  content_items: Array<{ id: string; title: string; url: string; text: string }>
  evidence: Evidence[]
  sales_elements: SalesElement[]
  gaps: Gap[]
  jobs: Array<{ id: string; job_type: string; status: string; progress: number }>
}
