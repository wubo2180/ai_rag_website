const toText = (value) => {
  if (value === null || value === undefined) return ''
  return String(value).trim()
}

const PRODUCT_KEYS = ['product_name', 'product', '产品', '产品（中间体配比）', '产品(中间体配比)']

const firstValue = (source, keys) => {
  if (!source || typeof source !== 'object') return ''
  for (const key of keys) {
    const value = source[key]
    if (value !== undefined && value !== null && value !== '') {
      return value
    }
  }
  return ''
}

const ensureArray = (value) => {
  if (Array.isArray(value)) return value
  if (value && typeof value === 'object') {
    if (Array.isArray(value.rows)) return value.rows
    if (Array.isArray(value.data)) return value.data
    if (Array.isArray(value.items)) return value.items
  }
  return []
}

const slugify = (value, fallbackIndex) => {
  const base = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '_')
    .replace(/^_+|_+$/g, '')
  return base || `metric_${fallbackIndex}`
}

export const createPaperTemplate = (title = '') => ({
  template_type: 'paper_material_v2',
  basic_info: {
    article_id: '',
    article_name: toText(title),
    article_doi: '',
    publish_year: '',
  },
  materials: [],
  preparation_process: '',
  intermediates: [],
  properties: {
    columns: [],
    rows: [],
  },
  notes: '',
})

const normalizeMaterialRow = (row) => ({
  material_id: toText(firstValue(row, ['material_id', '原料编号', '材料编号'])),
  material_name: toText(firstValue(row, ['material_name', '原料名称', '材料名称'])),
  material_characteristic: toText(firstValue(row, ['material_characteristic', '原料特性', '材料特性', 'characteristic'])),
  cas_number: toText(firstValue(row, ['cas_number', 'cas', 'CAS', 'CAS号'])),
})

const normalizeIntermediateRow = (row) => ({
  intermediate_id: toText(firstValue(row, ['intermediate_id', '中间体编号'])),
  formula: toText(firstValue(row, ['formula', '配方', 'intermediate_composition', '中间体组成', 'intermediate_name', '中间体名称'])),
})

const normalizePropertyTable = (value) => {
  const normalized = {
    columns: [],
    rows: [],
  }

  if (value && typeof value === 'object' && Array.isArray(value.columns) && Array.isArray(value.rows)) {
    normalized.columns = value.columns.map((column, index) => ({
      key: toText(column?.key) || slugify(column?.name, index + 1),
      name: toText(column?.name) || `性能${index + 1}`,
    }))
    normalized.rows = value.rows.map((row) => {
      const productName = toText(firstValue(row, PRODUCT_KEYS))
      const values = {}
      normalized.columns.forEach((column) => {
        values[column.key] = toText(row?.values?.[column.key] ?? row?.[column.key])
      })
      return {
        product_name: productName,
        values,
      }
    })
    return normalized
  }

  const rows = ensureArray(value).filter((item) => item && typeof item === 'object')
  if (!rows.length) {
    return normalized
  }

  const columnMap = new Map()
  rows.forEach((row) => {
    Object.keys(row).forEach((key) => {
      if (PRODUCT_KEYS.includes(key)) return
      const label = toText(key)
      if (!label) return
      if (!columnMap.has(label)) {
        columnMap.set(label, {
          key: slugify(label, columnMap.size + 1),
          name: label,
        })
      }
    })
  })

  normalized.columns = Array.from(columnMap.values())
  normalized.rows = rows.map((row) => {
    const productName = toText(firstValue(row, PRODUCT_KEYS))
    const values = {}
    normalized.columns.forEach((column) => {
      values[column.key] = toText(row?.[column.name])
    })
    return {
      product_name: productName,
      values,
    }
  })

  return normalized
}

const buildLegacyPropertyTable = (legacyRows) => {
  const columns = []
  const columnMap = new Map()
  const rows = []

  legacyRows.forEach((item, index) => {
    const row = {
      product_name: toText(item?.intermediate_name || item?.intermediate_id || item?.material_name || `样品${index + 1}`),
      values: {},
    }

    const properties = Array.isArray(item?.properties) ? item.properties : []
    properties.forEach((property) => {
      const label = toText(property?.property_name || property?.property_id)
      if (!label) return
      if (!columnMap.has(label)) {
        const column = {
          key: slugify(label, columnMap.size + 1),
          name: label,
        }
        columnMap.set(label, column)
        columns.push(column)
      }
      row.values[columnMap.get(label).key] = toText(property?.property_value)
    })

    rows.push(row)
  })

  return { columns, rows }
}

export const hasPaperShape = (payload) => {
  if (!payload || typeof payload !== 'object') return false
  return Boolean(
    payload.basic_info
    || Array.isArray(payload.materials)
    || Array.isArray(payload.intermediates)
    || payload.properties
    || payload.article_id
    || payload.article_name
    || Array.isArray(payload.hierarchical_data)
    || Array.isArray(payload.material_intermediates),
  )
}

export const normalizePaperData = (payload = {}, title = '') => {
  const base = createPaperTemplate(title)
  if (!payload || typeof payload !== 'object') {
    return base
  }

  if (
    payload.basic_info
    || Array.isArray(payload.materials)
    || Array.isArray(payload.intermediates)
    || payload.properties
    || payload.preparation_process
    || payload.notes
  ) {
    const basic = payload.basic_info && typeof payload.basic_info === 'object' ? payload.basic_info : payload
    base.basic_info.article_id = toText(firstValue(basic, ['article_id', '文献编号']))
    base.basic_info.article_name = toText(firstValue(basic, ['article_name', '文献名称'])) || toText(title)
    base.basic_info.article_doi = toText(firstValue(basic, ['article_doi', '文献DOI号', 'doi', 'DOI']))
    base.basic_info.publish_year = toText(firstValue(basic, ['publish_year', '文献出版年份', '出版年份', 'year']))

    base.materials = ensureArray(payload.materials || payload['原材料']).map(normalizeMaterialRow)
    base.preparation_process = toText(firstValue(payload, ['preparation_process', '制备工艺', 'process_description']))
    base.intermediates = ensureArray(payload.intermediates || payload['中间体']).map(normalizeIntermediateRow)
    base.properties = normalizePropertyTable(payload.properties || payload['性能'])
    base.notes = toText(firstValue(payload, ['notes', '备注', 'remark']))
    return base
  }

  const hierarchy = Array.isArray(payload.hierarchical_data)
    ? payload.hierarchical_data
    : (Array.isArray(payload.material_intermediates) ? payload.material_intermediates : [])

  base.basic_info.article_id = toText(firstValue(payload, ['article_id', '文献编号']))
  base.basic_info.article_name = toText(firstValue(payload, ['article_name', '文献名称'])) || toText(title)
  base.notes = toText(firstValue(payload, ['performance_trend', 'notes', '备注']))

  const materialSeen = new Set()
  base.materials = hierarchy
    .map((item) => normalizeMaterialRow(item))
    .filter((item) => {
      const key = `${item.material_id}|${item.material_name}|${item.cas_number}`
      if (!item.material_id && !item.material_name && !item.material_characteristic && !item.cas_number) return false
      if (materialSeen.has(key)) return false
      materialSeen.add(key)
      return true
    })

  const intermediateSeen = new Set()
  base.intermediates = hierarchy
    .map((item) => normalizeIntermediateRow(item))
    .filter((item) => {
      const key = `${item.intermediate_id}|${item.formula}`
      if (!item.intermediate_id && !item.formula) return false
      if (intermediateSeen.has(key)) return false
      intermediateSeen.add(key)
      return true
    })

  base.properties = buildLegacyPropertyTable(hierarchy)
  return base
}

export const hasMeaningfulPaperData = (payload, title = '') => {
  if (!hasPaperShape(payload)) return false
  const normalized = normalizePaperData(payload, title)
  if (toText(normalized.basic_info.article_id)) return true
  if (toText(normalized.basic_info.article_doi)) return true
  if (toText(normalized.basic_info.publish_year)) return true
  if (normalized.materials.length) return true
  if (toText(normalized.preparation_process)) return true
  if (normalized.intermediates.length) return true
  if (normalized.properties.columns.length || normalized.properties.rows.length) return true
  if (toText(normalized.notes)) return true

  const articleName = toText(normalized.basic_info.article_name)
  return Boolean(articleName && articleName !== toText(title))
}

const collectTextSegments = (value) => {
  const text = toText(value)
  if (!text) return []

  return text
    .split(/[\n\r;；。!！?？,，]/)
    .map((item) => item.trim())
    .filter((item) => item.length >= 2 && item.length <= 80)
}

export const buildPaperHighlightTerms = (payload, title = '') => {
  const normalized = normalizePaperData(payload, title)
  const terms = []

  const pushTerm = (value) => {
    const text = toText(value)
    if (!text) return
    if (text.length < 2) return
    if (text.length > 120) return
    terms.push(text)
  }

  pushTerm(normalized.basic_info.article_id)
  pushTerm(normalized.basic_info.article_name)
  pushTerm(normalized.basic_info.article_doi)
  pushTerm(normalized.basic_info.publish_year)

  normalized.materials.forEach((item) => {
    pushTerm(item.material_id)
    pushTerm(item.material_name)
    pushTerm(item.material_characteristic)
    pushTerm(item.cas_number)
  })

  collectTextSegments(normalized.preparation_process).forEach(pushTerm)

  normalized.intermediates.forEach((item) => {
    pushTerm(item.intermediate_id)
    pushTerm(item.formula)
  })

  normalized.properties.rows.forEach((row) => {
    pushTerm(row.product_name)
    Object.values(row.values || {}).forEach(pushTerm)
  })

  collectTextSegments(normalized.notes).forEach(pushTerm)

  return Array.from(new Set(terms))
    .sort((left, right) => right.length - left.length)
}
