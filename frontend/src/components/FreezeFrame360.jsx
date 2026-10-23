import React from 'react';

/**
 * frontend/src/components/FreezeFrame360.jsx
 * Renderizador SVG de Geometría Computacional sobre instantáneas StatsBomb 360:
 * - Cono de visión de cámara (visible_area)
 * - Teselación de Voronoi recortada (voronoi_cells)
 * - Triangulación de Delaunay (delaunay_edges)
 * - Polígono de Compacidad Convex Hull (hull_vertices + área en m^2)
 * - Radio de asfixia espacial de 3m (3.28 yd) y vector de pase de ruptura
 */
export default function FreezeFrame360({
  event360,
  showVoronoi = true,
  showConvexHull = true,
  showDelaunay = false,
  showVisibleArea = true,
}) {
  if (!event360 || !event360.freeze_frame) return null;

  const {
    freeze_frame = [],
    visible_area = [],
    geometry = {},
    start_x,
    start_y,
    end_x,
    end_y,
    ball_x,
    ball_y,
    defenders_broken,
    suffocation_3m,
  } = event360;

  const {
    hull_vertices = [],
    hull_area_m2 = 0,
    centroid_x = 60,
    centroid_y = 40,
    delaunay_edges = [],
    voronoi_cells = [],
  } = geometry || {};

  const bx = start_x ?? ball_x;
  const by = start_y ?? ball_y;

  const visiblePolygonPoints =
    Array.isArray(visible_area) && visible_area.length >= 3
      ? visible_area.map((pt) => `${pt[0]},${pt[1]}`).join(' ')
      : null;

  const hullPolygonPoints =
    Array.isArray(hull_vertices) && hull_vertices.length >= 3
      ? hull_vertices.map((pt) => `${pt[0]},${pt[1]}`).join(' ')
      : null;

  return (
    <g className="freeze-frame-360-layer">
      {/* 1. Cono de Visión de Cámara 360 */}
      {showVisibleArea && visiblePolygonPoints && (
        <polygon
          points={visiblePolygonPoints}
          fill="#8B5CF6"
          fillOpacity="0.06"
          stroke="#8B5CF6"
          strokeWidth="0.35"
          strokeDasharray="1.5 1.2"
        />
      )}

      {/* 2. Teselación de Voronoi (Control Espacial 360) */}
      {showVoronoi &&
        voronoi_cells.map((cell, idx) => {
          const polyStr = (cell.polygon || []).map((p) => `${p[0]},${p[1]}`).join(' ');
          if (!polyStr) return null;
          const isOwn = cell.is_target_team;
          return (
            <polygon
              key={`vor-${idx}`}
              points={polyStr}
              fill={isOwn ? '#00F5D4' : '#F43F5E'}
              fillOpacity={cell.actor ? '0.22' : '0.09'}
              stroke={isOwn ? '#00F5D4' : '#F43F5E'}
              strokeOpacity="0.45"
              strokeWidth="0.25"
            />
          );
        })}

      {/* 3. Triangulación de Delaunay (Conectividad Estructural Propia) */}
      {showDelaunay &&
        delaunay_edges.map((edge, idx) => (
          <line
            key={`del-${idx}`}
            x1={edge[0][0]}
            y1={edge[0][1]}
            x2={edge[1][0]}
            y2={edge[1][1]}
            stroke="#00F5D4"
            strokeOpacity="0.45"
            strokeWidth="0.28"
            strokeDasharray="0.8 0.8"
          />
        ))}

      {/* 4. Polígono Convex Hull (Compacidad del Bloque en m^2) */}
      {showConvexHull && hullPolygonPoints && (
        <g>
          <polygon
            points={hullPolygonPoints}
            fill="#8B5CF6"
            fillOpacity="0.18"
            stroke="#8B5CF6"
            strokeWidth="0.55"
          />
          {hull_area_m2 > 0 && (
            <g transform={`translate(${centroid_x}, ${centroid_y})`}>
              <rect
                x="-11.5"
                y="-3.2"
                width="23"
                height="4.6"
                rx="1.1"
                fill="#0B0F19"
                fillOpacity="0.88"
                stroke="#8B5CF6"
                strokeWidth="0.3"
              />
              <text
                x="0"
                y="-0.3"
                textAnchor="middle"
                fill="#E2E8F0"
                fontSize="2.2"
                fontFamily="JetBrains Mono, monospace"
                fontWeight="bold"
              >
                {`Hull: ${hull_area_m2} m²`}
              </text>
            </g>
          )}
        </g>
      )}

      {/* 5. Radio de Asfixia Espacial (3m = 3.28 yd) o Vector de Pase de Ruptura */}
      {bx != null && by != null && (
        <g>
          <circle
            cx={bx}
            cy={by}
            r={3.28}
            fill="#F59E0B"
            fillOpacity="0.15"
            stroke="#F59E0B"
            strokeWidth="0.35"
            strokeDasharray="0.8 0.6"
          />
          {end_x != null && end_y != null && (
            <g>
              {/* Cono de ruptura entre pasador y receptor */}
              <line
                x1={bx}
                y1={by}
                x2={end_x}
                y2={end_y}
                stroke="#00F5D4"
                strokeWidth="0.85"
                markerEnd="url(#arrow-cyan)"
              />
              <circle
                cx={end_x}
                cy={end_y}
                r="1.4"
                fill="#00F5D4"
                stroke="#0B0F19"
                strokeWidth="0.35"
              />
            </g>
          )}
        </g>
      )}

      {/* 6. Jugadores en el Freeze Frame 360 */}
      {freeze_frame.map((pt, idx) => {
        const px = pt.target_x ?? pt.x;
        const py = pt.target_y ?? pt.y;
        const isOwn = pt.is_target_team;
        const isActor = pt.actor;
        const isGK = pt.keeper;

        let fillColor = isOwn ? '#00F5D4' : '#F43F5E';
        if (isGK) fillColor = isOwn ? '#38BDF8' : '#FB7185';
        if (isActor) fillColor = '#F59E0B';

        return (
          <g key={`ff-pt-${idx}`} transform={`translate(${px}, ${py})`}>
            {isActor && (
              <circle
                r="2.4"
                fill="none"
                stroke="#F59E0B"
                strokeWidth="0.4"
              />
            )}
            <circle
              r={isActor ? '1.55' : '1.3'}
              fill={fillColor}
              stroke="#0B0F19"
              strokeWidth="0.38"
            />
            {isGK && (
              <text
                y="0.55"
                textAnchor="middle"
                fill="#0B0F19"
                fontSize="1.35"
                fontWeight="bold"
                fontFamily="JetBrains Mono, monospace"
              >
                GK
              </text>
            )}
          </g>
        );
      })}

      {/* 7. Micro-anotación superior en cancha */}
      {bx != null && by != null && (defenders_broken > 0 || suffocation_3m != null) && (
        <g transform={`translate(${Math.min(102, Math.max(18, bx))}, ${Math.max(6, by - 5.5)})`}>
          <rect
            x="-14"
            y="-2.8"
            width="28"
            height="4.4"
            rx="1"
            fill="#0B0F19"
            fillOpacity="0.92"
            stroke="#00F5D4"
            strokeWidth="0.3"
          />
          <text
            x="0"
            y="-0.1"
            textAnchor="middle"
            fill="#00F5D4"
            fontSize="2.0"
            fontFamily="JetBrains Mono, monospace"
            fontWeight="bold"
          >
            {defenders_broken > 0
              ? `⚡ ${defenders_broken} Defensores Superados`
              : `🔥 Asfixia 3m: ${suffocation_3m} Def.`}
          </text>
        </g>
      )}
    </g>
  );
}
