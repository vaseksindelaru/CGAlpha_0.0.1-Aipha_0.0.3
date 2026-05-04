import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup_proposals")

def cleanup():
    entries_dir = Path('cgalpha_v3/memory/memory_entries')
    if not entries_dir.exists():
        logger.error(f"Directory {entries_dir} not found")
        return

    count = 0
    deleted = 0
    targets = {'volume_threshold', 'n_estimators'}

    logger.info(f"Scanning {entries_dir}...")
    
    for f in entries_dir.glob('*.json'):
        count += 1
        try:
            with open(f, 'r') as file:
                data = json.load(file)
            
            content_str = data.get('content', '{}')
            content = json.loads(content_str)
            
            if content.get('status') == 'pending':
                spec = content.get('spec', {})
                attr = spec.get('target_attribute')
                
                if attr in targets:
                    f.unlink()
                    deleted += 1
                    if deleted % 50 == 0:
                        logger.info(f"Deleted {deleted} pending proposals matchings targets...")
        except Exception as e:
            logger.error(f"Error processing {f.name}: {e}")
            continue

    logger.info(f"Cleanup finished. Total scanned: {count}, Total deleted: {deleted}")

if __name__ == '__main__':
    cleanup()
