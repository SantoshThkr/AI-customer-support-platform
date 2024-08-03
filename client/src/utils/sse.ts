export interface SSEEvent {
  event: string
  data: unknown
}

/**
 * Split buffered text into complete SSE events. Returns the parsed events and
 * whatever incomplete text is left over for the next read.
 */
export function parseSSE(buffer: string): { events: SSEEvent[]; rest: string } {
  const events: SSEEvent[] = []
  const blocks = buffer.replace(/\r\n/g, '\n').split('\n\n')
  const rest = blocks.pop() ?? ''

  for (const block of blocks) {
    let event = 'message'
    const dataLines: string[] = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart())
    }
    if (dataLines.length === 0) continue
    const raw = dataLines.join('\n')
    try {
      events.push({ event, data: JSON.parse(raw) })
    } catch {
      events.push({ event, data: raw })
    }
  }
  return { events, rest }
}
