import { useEffect, useRef } from 'react';
import { useAppStore } from '../../../store/useAppStore';
import { mapNodes, mapRoutes, landMasses } from '../../../data/mockData';

const MapTab = () => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const { mapStatus, mapRoute, truckPhase, truckProgress, phases } = useAppStore();

  // Canvas drawing functions
  const resizeCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const parent = canvas.parentElement;
    if (!parent) return;
    
    const rect = parent.getBoundingClientRect();
    const devicePixelRatio = window.devicePixelRatio || 1;
    
    // Set actual size in memory (scaled to account for extra pixel density)
    canvas.width = rect.width * devicePixelRatio;
    canvas.height = rect.height * devicePixelRatio;
    
    // Set display size (css pixels)
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    
    // Scale the drawing context so everything draws at the correct size
    const ctx = canvas.getContext('2d');
    ctx.scale(devicePixelRatio, devicePixelRatio);
  };

  const px = (key, canvas) => {
    const rect = canvas.getBoundingClientRect();
    return {
      x: mapNodes[key].x * rect.width,
      y: mapNodes[key].y * rect.height
    };
  };

  const cp = (a, b, canvas) => {
    const rect = canvas.getBoundingClientRect();
    const dist = Math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2);
    const curve = dist > 180 ? -0.22 : -0.04;
    return {
      x: (a.x + b.x) / 2,
      y: (a.y + b.y) / 2 + curve * rect.height
    };
  };

  const bezPt = (p0, p1, c, t) => ({
    x: (1 - t) ** 2 * p0.x + 2 * (1 - t) * t * c.x + t ** 2 * p1.x,
    y: (1 - t) ** 2 * p0.y + 2 * (1 - t) * t * c.y + t ** 2 * p1.y
  });

  const drawLand = (ctx, canvas) => {
    const rect = canvas.getBoundingClientRect();
    ctx.fillStyle = 'rgba(0,212,255,0.038)';
    ctx.strokeStyle = 'rgba(0,212,255,0.10)';
    ctx.lineWidth = 0.8;
    
    landMasses.forEach(pts => {
      ctx.beginPath();
      ctx.moveTo(pts[0][0] * rect.width, pts[0][1] * rect.height);
      for (let i = 1; i < pts.length; i++) {
        ctx.lineTo(pts[i][0] * rect.width, pts[i][1] * rect.height);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  };

  const drawRoutes = (ctx, canvas, dashOffset) => {
    mapRoutes.forEach(route => {
      const a = px(route.a, canvas);
      const b = px(route.b, canvas);
      const c = cp(a, b, canvas);
      
      ctx.beginPath();
      ctx.setLineDash(route.dash);
      ctx.lineDashOffset = -dashOffset;
      ctx.lineWidth = 1.6;
      
      if (route.state === 'blocked') ctx.strokeStyle = 'rgba(255,59,92,0.58)';
      else if (route.state === 'active') ctx.strokeStyle = 'rgba(0,212,255,0.62)';
      else if (route.state === 'proposed') ctx.strokeStyle = 'rgba(255,179,64,0.38)';
      
      ctx.moveTo(a.x, a.y);
      ctx.quadraticCurveTo(c.x, c.y, b.x, b.y);
      ctx.stroke();
      ctx.setLineDash([]);
    });
  };

  const drawNodes = (ctx, canvas, time) => {
    Object.keys(mapNodes).forEach(key => {
      const node = mapNodes[key];
      const p = px(key, canvas);
      const pulse = Math.sin(time + key.length * 0.8) * 0.5 + 0.5;
      const isBlocked = key === 'longbeach';
      const isDest = key === 'austin';
      
      // Glow
      if (isBlocked || isDest) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 10 + pulse * 5, 0, Math.PI * 2);
        ctx.fillStyle = isBlocked 
          ? `rgba(255,59,92,${pulse * 0.12})` 
          : `rgba(0,230,118,${pulse * 0.1})`;
        ctx.fill();
      }
      
      // Dot
      ctx.beginPath();
      ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = isBlocked 
        ? 'rgba(255,59,92,0.3)' 
        : isDest 
          ? 'rgba(0,230,118,0.25)' 
          : 'rgba(0,212,255,0.18)';
      ctx.fill();
      ctx.strokeStyle = node.color;
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // Label
      const label = `${node.icon} ${node.label}`;
      ctx.font = '10px "JetBrains Mono", monospace';
      const tw = ctx.measureText(label).width;
      const lx = p.x - tw / 2 - 4;
      const ly = p.y - 20;
      
      ctx.fillStyle = 'rgba(4,8,16,0.82)';
      ctx.beginPath();
      ctx.roundRect ? ctx.roundRect(lx, ly, tw + 8, 14, 3) : ctx.rect(lx, ly, tw + 8, 14);
      ctx.fill();
      ctx.strokeStyle = node.color;
      ctx.lineWidth = 0.6;
      ctx.stroke();
      ctx.fillStyle = node.color;
      ctx.fillText(label, p.x - tw / 2, ly + 10);
    });
  };

  const drawTruck = (ctx, canvas, now) => {
    if (truckPhase === 'blocked') {
      const p = px('longbeach', canvas);
      const wobble = Math.sin(now / 900) * 3;
      ctx.font = '13px serif';
      ctx.fillText('🚛', p.x + 8 + wobble, p.y + 4);
      ctx.font = '8px "JetBrains Mono", monospace';
      ctx.fillStyle = 'rgba(255,59,92,0.9)';
      ctx.fillText('HELD', p.x + 6, p.y - 7);
    } else if (truckPhase === 'flying') {
      const a = px('longbeach', canvas);
      const b = px('lax', canvas);
      const c = cp(a, b, canvas);
      const p = bezPt(a, b, c, truckProgress);
      
      ctx.beginPath();
      ctx.arc(p.x, p.y, 11, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,212,255,0.1)';
      ctx.fill();
      ctx.font = '14px serif';
      ctx.fillText('🛫', p.x - 8, p.y + 6);
    } else if (truckPhase === 'driving') {
      const a = px('lax', canvas);
      const b = px('austin', canvas);
      const c = cp(a, b, canvas);
      const p = bezPt(a, b, c, truckProgress);
      
      ctx.beginPath();
      ctx.arc(p.x, p.y, 11, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,212,255,0.1)';
      ctx.fill();
      ctx.font = '14px serif';
      ctx.fillText('🚛', p.x - 8, p.y + 6);
    } else if (truckPhase === 'arrived') {
      const d = px('austin', canvas);
      ctx.font = '14px serif';
      ctx.fillText('✅', d.x - 7, d.y - 14);
      ctx.font = '8px "JetBrains Mono", monospace';
      ctx.fillStyle = 'rgba(0,230,118,0.9)';
      ctx.fillText('DELIVERED', d.x - 18, d.y - 20);
    }
  };

  const drawMap = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const now = Date.now();
    const dashOffset = (now * 0.35 / 1000) % 22;
    const time = now / 500;
    
    ctx.clearRect(0, 0, rect.width, rect.height);
    
    // Background gradient
    const g = ctx.createRadialGradient(
      rect.width * 0.25, rect.height * 0.5, 0,
      rect.width * 0.25, rect.height * 0.5, rect.width * 0.7
    );
    g.addColorStop(0, 'rgba(0,40,70,0.4)');
    g.addColorStop(1, 'rgba(4,8,16,1)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, rect.width, rect.height);
    
    // Grid
    ctx.strokeStyle = 'rgba(0,212,255,0.03)';
    ctx.lineWidth = 0.5;
    for (let x = 0; x < rect.width; x += rect.width / 9) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, rect.height);
      ctx.stroke();
    }
    for (let y = 0; y < rect.height; y += rect.height / 6) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(rect.width, y);
      ctx.stroke();
    }
    
    drawLand(ctx, canvas);
    drawRoutes(ctx, canvas, dashOffset);
    drawNodes(ctx, canvas, time);
    drawTruck(ctx, canvas, now);
    
    animationRef.current = requestAnimationFrame(drawMap);
  };

  useEffect(() => {
    let resizeTimeout;
    
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        resizeCanvas();
      }, 100);
    };
    
    resizeCanvas();
    drawMap();
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      clearTimeout(resizeTimeout);
      window.removeEventListener('resize', handleResize);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [truckPhase, truckProgress]);

  useEffect(() => {
    // Start animation loop
    drawMap();
  }, []);

  const getStatusColor = () => {
    switch (mapStatus) {
      case 'AGENTS ACTIVE': return '#ffb340';
      case 'RISK FLAGGED': return '#ff3b5c';
      case 'EXECUTING': return '#00e676';
      case 'DELIVERED ✅': return '#00e676';
      default: return '#ffb340';
    }
  };

  return (
    <div className="flex-1 relative overflow-hidden bg-[#040810]">
      {/* Map Bar */}
      <div className="absolute top-0 left-0 right-0 flex z-10 border-b border-[rgba(29,45,64,0.8)]">
        <div className="flex-1 p-[7px_11px] bg-[rgba(4,8,16,0.88)] border-r border-[rgba(29,45,64,0.8)]">
          <div className="text-[8px] text-[#3d5a72] uppercase tracking-wide font-mono">Origin</div>
          <div className="font-mono text-xs font-bold text-[#7aa0be] mt-[1px]">📦 Shanghai Port</div>
        </div>
        <div className="flex-1 p-[7px_11px] bg-[rgba(4,8,16,0.88)] border-r border-[rgba(29,45,64,0.8)]">
          <div className="text-[8px] text-[#3d5a72] uppercase tracking-wide font-mono">Blocked At</div>
          <div className="font-mono text-xs font-bold text-[#ff3b5c] mt-[1px]">🔴 Long Beach</div>
        </div>
        <div className="flex-1 p-[7px_11px] bg-[rgba(4,8,16,0.88)] border-r border-[rgba(29,45,64,0.8)]">
          <div className="text-[8px] text-[#3d5a72] uppercase tracking-wide font-mono">Active Route</div>
          <div className="font-mono text-xs font-bold text-[#00d4ff] mt-[1px]">{mapRoute}</div>
        </div>
        <div className="flex-1 p-[7px_11px] bg-[rgba(4,8,16,0.88)]">
          <div className="text-[8px] text-[#3d5a72] uppercase tracking-wide font-mono">Status</div>
          <div 
            className="font-mono text-xs font-bold mt-[1px]"
            style={{ color: getStatusColor() }}
          >
            {mapStatus}
          </div>
        </div>
      </div>

      {/* Canvas */}
      <canvas 
        ref={canvasRef}
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ 
          maxWidth: '100%',
          maxHeight: '100%',
          objectFit: 'contain'
        }}
      />

      {/* Phase Bar */}
      <div className="absolute bottom-0 left-0 right-0 bg-[rgba(4,8,16,0.9)] border-t border-[rgba(29,45,64,0.8)] p-[6px_14px] flex items-center gap-3 z-10">
        <div className="text-[8px] text-[#3d5a72] uppercase tracking-wide font-mono flex-shrink-0">
          Phase
        </div>
        <div className="flex items-center gap-[3px] flex-1">
          {phases.map((phase, index) => (
            <div key={phase.id} className="flex items-center gap-1">
              {index > 0 && <div className="text-[#1d2d40] text-[9px] mx-1">→</div>}
              <div className={`flex items-center gap-1 text-[9px] font-mono whitespace-nowrap ${
                phase.status === 'done' ? 'text-[#00e676]' :
                phase.status === 'active' ? 'text-[#00d4ff]' : 'text-[#3d5a72]'
              }`}>
                <div className={`w-[7px] h-[7px] rounded-full ${
                  phase.status === 'done' ? 'bg-[#00e676]' :
                  phase.status === 'active' ? 'bg-[#00d4ff] animate-pulse' : 'bg-[#1d2d40]'
                }`}></div>
                {phase.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MapTab;
