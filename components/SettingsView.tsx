'use client'

import React from "react"

import { useEffect, useState, useCallback } from 'react'
import { Activity, Brain, Database, Zap, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import type { SystemHealthResponse } from '@/app/api/v1/system/health/route'

interface HealthIndicatorProps {
  label: string
  sublabel: string
  status: 'online' | 'offline' | 'connected' | 'disconnected' | 'active' | 'sleeping' | 'processing' | 'degraded' | 'error'
  latency?: number
  icon: React.ReactNode
  pulseColor: string
  accentColor: string
}

function HealthIndicator({ label, sublabel, status, latency, icon, pulseColor, accentColor }: HealthIndicatorProps) {
  const getStatusEmoji = () => {
    switch (status) {
      case 'online':
      case 'connected':
      case 'active':
        return '🟢'
      case 'sleeping':
        return '💤'
      case 'processing':
        return '⚡'
      case 'degraded':
        return '🟡'
      case 'offline':
      case 'disconnected':
      case 'error':
        return '🔴'
      default:
        return '⚪'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'online':
        return 'Online'
      case 'connected':
        return latency ? `Connected (${latency}ms)` : 'Connected'
      case 'active':
        return 'Active'
      case 'sleeping':
        return 'Sleeping'
      case 'processing':
        return 'Processing'
      case 'degraded':
        return 'Degraded'
      case 'offline':
        return 'Offline'
      case 'disconnected':
        return 'Disconnected'
      case 'error':
        return 'Error'
      default:
        return 'Unknown'
    }
  }

  const isActive = status === 'online' || status === 'connected' || status === 'active'

  return (
    <div className="relative group">
      {/* Glow effect */}
      <div 
        className={`absolute -inset-0.5 rounded-lg opacity-30 blur-sm transition-opacity duration-300 group-hover:opacity-60 ${isActive ? pulseColor : 'bg-neutral-600'}`}
      />
      
      <div className="relative flex items-center gap-4 p-4 rounded-lg bg-neutral-900/80 border border-neutral-800 backdrop-blur-sm">
        {/* Icon with pulse animation */}
        <div className="relative">
          <div 
            className={`w-12 h-12 rounded-lg flex items-center justify-center ${accentColor} bg-opacity-20 border border-current`}
            style={{ borderColor: 'currentColor', borderOpacity: 0.3 }}
          >
            {icon}
          </div>
          {isActive && (
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${pulseColor} opacity-75`} />
              <span className={`relative inline-flex rounded-full h-3 w-3 ${pulseColor}`} />
            </span>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-neutral-100 truncate">{label}</h3>
            <span className="text-xs text-neutral-500">({sublabel})</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-lg">{getStatusEmoji()}</span>
            <span className={`text-sm font-mono ${isActive ? accentColor : 'text-neutral-500'}`}>
              {getStatusText()}
            </span>
          </div>
        </div>

        {/* Latency bar for connected services */}
        {latency !== undefined && (
          <div className="flex flex-col items-end gap-1">
            <span className="text-xs text-neutral-500">Latency</span>
            <div className="w-16 h-1.5 bg-neutral-800 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  latency < 30 ? 'bg-emerald-500' : latency < 60 ? 'bg-amber-500' : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(latency / 100 * 100, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ScanlineOverlay() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-xl">
      <div className="absolute inset-0 bg-[linear-gradient(transparent_50%,rgba(0,255,136,0.03)_50%)] bg-[length:100%_4px] animate-[scanline_8s_linear_infinite]" />
    </div>
  )
}

function GridPattern() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-xl opacity-10">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,255,136,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,255,136,0.1)_1px,transparent_1px)] bg-[size:20px_20px]" />
    </div>
  )
}

export default function SettingsView() {
  const [health, setHealth] = useState<SystemHealthResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchHealth = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch('/api/v1/system/health')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data: SystemHealthResponse = await response.json()
      setHealth(data)
      setLastRefresh(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [fetchHealth])

  const allOnline = health && 
    health.brain.status === 'online' && 
    health.hippocampus.status === 'connected'

  return (
    <div className="relative w-full max-w-2xl mx-auto">
      {/* Outer glow */}
      <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 via-cyan-500/20 to-purple-500/20 rounded-2xl blur-xl opacity-50" />
      
      <div className="relative rounded-xl bg-neutral-950 border border-neutral-800 overflow-hidden">
        <GridPattern />
        <ScanlineOverlay />
        
        {/* Header */}
        <div className="relative flex items-center justify-between p-4 border-b border-neutral-800 bg-neutral-900/50">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Activity className="w-6 h-6 text-emerald-400" />
              {allOnline && (
                <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                </span>
              )}
            </div>
            <div>
              <h2 className="text-lg font-bold text-neutral-100 tracking-wide">
                SYSTEM_HEALTH
              </h2>
              <p className="text-xs text-neutral-500 font-mono">
                LifeOS v3.1 :: Neural Interface Monitor
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Connection status */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-neutral-900 border border-neutral-700">
              {allOnline ? (
                <>
                  <Wifi className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-mono text-emerald-400">SYNC</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-red-400" />
                  <span className="text-xs font-mono text-red-400">OFFLINE</span>
                </>
              )}
            </div>
            
            {/* Refresh button */}
            <button
              onClick={fetchHealth}
              disabled={isLoading}
              className="p-2 rounded-lg bg-neutral-900 border border-neutral-700 text-neutral-400 hover:text-emerald-400 hover:border-emerald-400/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="relative p-4 space-y-3">
          {error ? (
            <div className="flex items-center justify-center py-8 text-red-400">
              <div className="text-center">
                <WifiOff className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="font-mono text-sm">CONNECTION_ERROR: {error}</p>
                <button 
                  onClick={fetchHealth}
                  className="mt-3 px-4 py-2 text-xs font-mono bg-red-500/20 border border-red-500/50 rounded hover:bg-red-500/30 transition-colors"
                >
                  RETRY_CONNECTION
                </button>
              </div>
            </div>
          ) : isLoading && !health ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <div className="relative w-16 h-16 mx-auto mb-4">
                  <div className="absolute inset-0 border-2 border-emerald-500/30 rounded-full" />
                  <div className="absolute inset-0 border-2 border-emerald-400 rounded-full border-t-transparent animate-spin" />
                  <Brain className="absolute inset-0 m-auto w-6 h-6 text-emerald-400" />
                </div>
                <p className="font-mono text-sm text-emerald-400 animate-pulse">
                  INITIALIZING_NEURAL_LINK...
                </p>
              </div>
            </div>
          ) : health && (
            <>
              {/* Brain Status - FastAPI */}
              <HealthIndicator
                label="Brain Status"
                sublabel="FastAPI"
                status={health.brain.status}
                icon={<Brain className="w-6 h-6 text-cyan-400" />}
                pulseColor="bg-cyan-500"
                accentColor="text-cyan-400"
              />

              {/* Hippocampus - Supabase */}
              <HealthIndicator
                label="Hippocampus"
                sublabel="Supabase"
                status={health.hippocampus.status}
                latency={health.hippocampus.latency_ms}
                icon={<Database className="w-6 h-6 text-emerald-400" />}
                pulseColor="bg-emerald-500"
                accentColor="text-emerald-400"
              />

              {/* Evolution Agent */}
              <HealthIndicator
                label="Evolution Agent"
                sublabel="Self-Improvement Module"
                status={health.evolution_agent.status}
                icon={<Zap className="w-6 h-6 text-purple-400" />}
                pulseColor="bg-purple-500"
                accentColor="text-purple-400"
              />
            </>
          )}
        </div>

        {/* Footer */}
        <div className="relative flex items-center justify-between px-4 py-2 border-t border-neutral-800 bg-neutral-900/30">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-mono text-neutral-500">
              {lastRefresh 
                ? `Last sync: ${lastRefresh.toLocaleTimeString()}`
                : 'Awaiting sync...'
              }
            </span>
          </div>
          <span className="text-xs font-mono text-neutral-600">
            v3.1.0-alpha
          </span>
        </div>
      </div>
    </div>
  )
}
