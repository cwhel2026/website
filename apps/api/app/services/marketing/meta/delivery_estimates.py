"""Read-only Meta audience estimates. Missing/zero curves are not forecasts.

Source: https://developers.facebook.com/docs/graph-api/reference/ad-campaign/delivery_estimate/
"""
import re
from datetime import UTC, datetime
from app.services.marketing.meta_graph_client import graph_get


def parse_estimate(payload):
    rows = payload.get('data') if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return {'available': False, 'reason': 'No platform estimate returned'}
    row = rows[0]
    if row.get('estimate_ready') is not True:
        return {'available': False, 'reason': 'Platform estimate is not ready'}
    lower, upper = row.get('estimate_mau_lower_bound'), row.get('estimate_mau_upper_bound')
    if type(lower) is not int or type(upper) is not int or not 0 <= lower <= upper:
        return {'available': False, 'reason': 'Platform audience bounds unavailable'}
    return {'available': True, 'basis': 'Meta platform estimate, not verified performance', 'audience_lower': lower, 'audience_upper': upper, 'retrieved_at': datetime.now(UTC).isoformat(), 'note': 'Monthly eligible audience is not predicted unique campaign reach. Delivery curves are not assumed when unavailable.'}


async def fetch_delivery_estimate(adset_id):
    if not isinstance(adset_id, str) or not re.fullmatch(r'\d{1,40}', adset_id):
        return {'available': False, 'reason': 'A verified Meta ad set ID is required'}
    response = await graph_get(f'{adset_id}/delivery_estimate')
    if not response.get('ok'):
        return {'available': False, 'reason': 'Meta estimate request unavailable'}
    return parse_estimate(response.get('data'))
