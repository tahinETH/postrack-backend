import os
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
SOCIAL_DATA_API_KEY = os.getenv("SOCIAL_DATA_API_KEY")

class TwitterAPIClient:
    def __init__(self):
        self.api_key = SOCIAL_DATA_API_KEY
        
    def get_headers(self):
        
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }

    async def get_tweet_details(self,tweet_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f'https://api.socialdata.tools/twitter/tweets/{tweet_id}'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.get_headers()) as response:
                    return await response.json()
        except Exception as e:
            print(f"Error getting tweet details: {str(e)}")
            return None
    

if __name__ == "__main__":
    import random

    def get_random_names(count: int = 10) -> list[str]:
        names = [
            "balticbull", "bubadavit", "its2492", "WassieKid", "hyunhyynhynn",
            "ackwx", "LeBurns", "geomad", "haitaGL", "vicd85", "player12828",
            "Przemyk", "friendlyguy77", "PapaClarky", "HeyItsGilroy", "fugbeeple",
            "sakomal", "SirYoloo", "dende919", "MgrGracz", "bityann", "g1nt0ki",
            "TL0708", "free_wassie", "valerius_0x", "Nemo_where_is_dory", "Cucu0x",
            "Spons87", "cuba", "Davidvp2", "bernardp", "indianwassie", "wazziehunter",
            "Max", "Dan_Cool", "MikeFromEarth", "luiscordovadsgn", "t3chih21",
            "danscher", "LeChiffre420", "robotlegs99", "k_hooker", "tommykudoba",
            "LL00000000000", "baronroth", "AlejandroFer08", "Skinx_T", "dimalisk",
            "Chakingo", "simbaafx", "txngyy", "JGoogl", "zackattackworldtour"
        ]
        return random.sample(names, count)

    # Example usage
    random_names = get_random_names()
    print("Random 10 names:")
    for name in random_names:
        print(name)