# Estimación COCOMO II - La Condesa

## Resumen Ejecutivo

Este documento presenta la estimación de esfuerzo para el desarrollo del sistema web "La Condesa" utilizando el modelo COCOMO II (Constructive Cost Model II).

## Metodología

### Tipo de Proyecto
- **Categoría**: Midsize organic project
- **Reason**: Proyecto nuevo con experiencia en el equipo, utilizando tecnologías conocidas (Flask, Python, SQLite) con un tamaño medio de sistema

### Tamaño del Proyecto

#### Líneas de Código Estimadas (KLOC)

| Componente | Líneas de Código | Categoría |
|------------|------------------|-----------|
| Models | 1,200 | Organic |
| Routes | 2,500 | Organic |
| Services | 1,800 | Organic |
| Utilities | 600 | Organic |
| Templates | 4,000 | Organic |
| Static Assets | 1,000 | Organic |
| Configuration | 500 | Organic |
| **Total** | **11,600 LOC** | **~12 KLOC** |

### Factores de Esfuerzo (EF)

| Factor | Valor | Justificación |
|--------|-------|---------------|
| **PREL** (Requisitos previos) | 1.00 | Requisitos bien definidos |
| **CPEL** (Experiencia del equipo) | 0.86 | Equipo experimentado en Python/Flask |
| **TEAM** (Cohesión del equipo) | 1.00 | Equipo cohesionado |
| **PMAT** (Madurez del proceso) | 1.00 | Proceso establecido |
| **REUse** (Reutilización) | 1.10 | Uso de Flask, Bootstrap, SQLAlchemy |
| **RCPX** (Complejidad del producto) | 1.15 | Sistema web completo |
| **RUSE** (Requisitos de software) | 1.00 | Requisitos estándar |
| **PDAT** (Experiencia con la plataforma) | 0.87 | Conocimiento de Python/Flask |
| **PLEX** (Complejidad de la plataforma) | 1.00 | Plataforma conocida |
| **LTTR** (Conocimiento del lenguaje) | 0.86 | Python estándar |
| **TABR** (Requisitos de documentación) | 1.10 | Documentación completa requerida |

### Factor de Esfuerzo Total (EF)

```
EF = PREL × CPEL × TEAM × PMAT × REUse × RCPX × RUSE × PDAT × PLEX × LTTR × TABR
EF = 1.00 × 0.86 × 1.00 × 1.00 × 1.10 × 1.15 × 1.00 × 0.87 × 1.00 × 0.86 × 1.10
EF = 0.94
```

## Estimación de Esfuerjo

### Fórmula COCOMO II
```
E = a × (KLOC)^b × EF
```

### Parámetros (Proyecto Organic)
- **a** = 3.20
- **b** = 1.05

### Cálculo
```
E = 3.20 × (12)^1.05 × 0.94
E = 3.20 × 13.25 × 0.94
E = 39.9 person-months
```

### Resultado Final
- **Esfuerzo Estimado**: ~40 person-months (aprox. 1,000 horas)
- **Duración Estimada**: ~8-10 meses con equipo de 5 personas
- **Duración Estimada**: ~6-8 meses con equipo de 7 personas

## Desglose por Fase

| Fase | Porcentaje | Personas | Meses | Horas |
|------|------------|----------|-------|-------|
| **Requisitos** | 5% | 1 | 2 | 160 |
| **Diseño** | 10% | 1 | 4 | 320 |
| **Implementación** | 45% | 3 | 18 | 1,440 |
| **Pruebas** | 20% | 2 | 8 | 640 |
| **Documentación** | 10% | 1 | 4 | 320 |
| **Despliegue** | 5% | 1 | 2 | 160 |
| **TOTAL** | **100%** | | **~40** | **~3,040** |

## Supuestos

1. **Equipo**: 5-7 desarrolladores con experiencia en Python/Flask
2. **Requisitos**: Requisitos bien definidos en la fase de requisitos
3. **Tecnología**: Uso de tecnologías estándar (Flask, Bootstrap, SQLite)
4. **Infraestructura**: Servidores de desarrollo y producción disponibles
5. **Documentación**: Requerimientos completos de documentación
6. **Cambio de requisitos**: Controlado mediante proceso de gestión de cambios

## Riesgos Identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Cambios de requisitos frecuentes | Alta | Alto | Gestión rigurosa de cambios |
| Falta de experiencia en equipo | Media | Medio | Capacitación y mentoring |
| Complejidad del sistema | Media | Medio | Diseño modular y pruebas |
| Integridad de datos | Baja | Alto | Pruebas exhaustivas y respaldos |

## Notas

- Esta estimación es aproximada y puede variar +/- 25%
- Se recomienda revisión trimestral de estimaciones
- Considerar factores no técnicos (vacaciones, reuniones, etc.)
- Las horas de desarrollo real pueden variar según la experiencia del equipo

## Referencias

- COCOMO II Model Documentation
- IEEE 12207-2017 Systems and Software Engineering
- Boehm, B. et al. (2000). "Software Cost Estimation with Cocomo II"
