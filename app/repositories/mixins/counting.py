from typing import Optional, Dict, Any
from sqlalchemy import select, func, text
import hashlib
import json
import time

from app.schemas.pagination import ProductFilters


class OptimizedCountingMixin:
    """Mixin para conteos optimizados"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._count_cache = {}
        self._cache_ttl = 300  # 5 minutos

    async def get_approximate_count(self, filters: Optional[ProductFilters] = None) -> int:
        """Obtener conteo aproximado usando estadísticas de la tabla"""
        if not filters or not any([
            filters.is_active, filters.search, filters.min_price, 
            filters.max_price, filters.category_id, filters.category_ids
        ]):
            # Para conteo total sin filtros, usar estadísticas de PostgreSQL
            try:
                result = await self.db.execute(
                    text("""
                        SELECT reltuples::bigint AS estimate
                        FROM pg_class
                        WHERE relname = 'products'
                    """)
                )
                estimate = result.scalar()
                return max(estimate or 0, 0)
            except Exception:
                # Fallback a conteo normal si no es PostgreSQL
                return await self._get_exact_count(filters)
        
        return await self._get_cached_count(filters)

    async def _get_cached_count(self, filters: Optional[ProductFilters] = None) -> int:
        """Conteo con caché simple en memoria"""
        cache_key = self._generate_cache_key(filters)
        
        # Verificar caché
        if cache_key in self._count_cache:
            cached_data = self._count_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self._cache_ttl:
                return cached_data['count']
        
        # Obtener conteo real
        count = await self._get_exact_count(filters)
        
        # Guardar en caché
        self._count_cache[cache_key] = {
            'count': count,
            'timestamp': time.time()
        }
        
        return count

    async def _get_exact_count(self, filters: Optional[ProductFilters] = None) -> int:
        """Conteo exacto cuando es necesario"""
        from app.models.product import Product
        
        query = select(func.count(Product.id))
        query = self._apply_filters_to_count(query, filters)
        result = await self.db.execute(query)
        return result.scalar() or 0

    def _generate_cache_key(self, filters: Optional[ProductFilters]) -> str:
        """Generar clave de caché basada en filtros"""
        if not filters:
            return "no_filters"
        
        filter_dict = filters.dict(exclude_unset=True) if filters else {}
        filter_str = json.dumps(filter_dict, sort_keys=True)
        return hashlib.md5(filter_str.encode()).hexdigest()

    def _apply_filters_to_count(self, query, filters: Optional[ProductFilters]):
        """Aplicar filtros a query de conteo (implementar según tus filtros)"""
        # Esta función debe implementar la misma lógica de filtros
        # que tu método _apply_filters pero para queries de conteo
        if not filters:
            return query
            
        from app.models.product import Product
        from sqlalchemy import and_, or_
        
        conditions = []
        
        if filters.is_active is not None:
            conditions.append(Product.is_active == filters.is_active)
            
        if filters.search:
            search_term = f"%{filters.search.strip()}%"
            search_conditions = [
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            ]
            conditions.append(or_(*search_conditions))
            
        # Agregar más filtros según necesites...
        
        if conditions:
            query = query.where(and_(*conditions))
            
        return query