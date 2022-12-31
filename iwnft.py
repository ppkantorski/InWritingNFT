#!/usr/bin/env python3
import os, sys, requests, base64, random, pprint, re, time
# For using search by txhash
try:
    import web3
    USE_POLYGONSCAN = True
except:
    USE_POLYGONSCAN = False

# In Writing NFT Explorer
class InWritingNFTExplorer(object):
    def __init__(self):
        # User specified API-keys
        self.ALCHEMY_API_KEY = ""
        self.POLYGONSCAN_API_KEY = ""
        # API Urls
        self.ALCHEMY_API_URL = f"https://polygon-mainnet.g.alchemy.com/v2/{self.ALCHEMY_API_KEY}"
        self.POLYGONSCAN_API_URL = f"https://api.polygonscan.com/api?apikey={self.POLYGONSCAN_API_KEY}"
        # NFT Contract
        self.INWRITING_CONTRACT = "0x8fa77bFf25B6b557FA2d333b05C2De259Ce33eCA"
        
        # Internal NFT Data dict
        self.nft_data_dict = {'token_id':{},'wallet_address':{},'txhash':{}}
        
        if USE_POLYGONSCAN == False:
            self.POLYGONSCAN_API_KEY = ''
        
        self.print_on_load = False
    
    def get_nft_by_token(self, token_id):
        # This method requires an Alchemy API
        if self.ALCHEMY_API_KEY != '':
            method = "getNFTMetadata"
            alchemy_url = f"{self.ALCHEMY_API_URL}/{method}?contractAddress={self.INWRITING_CONTRACT}&tokenId={token_id}"
            alchemy_data = requests.get(alchemy_url).json()
            metadata = alchemy_data['metadata']
            if 'string' in metadata.keys():
                try:
                    nft_data = base64.b64decode(metadata['string']).decode('UTF')
                except:
                    nft_data = base64.b64decode(metadata['string']).decode('latin')
            else:
                self.invalid_param_warning(token_id)
                return None
            
            if nft_data != '':
                if self.print_on_load:
                    title = metadata['name']
                    self.print_nft_data(nft_data, title)
                #if token_id not in self.nft_data_dict['token_id'].keys():
                self.nft_data_dict['token_id'][token_id] = nft_data
                
                return self.nft_data_dict['token_id'][token_id]
            else:
                self.invalid_param_warning(token_id)
            
            
        else:
            self.missing_api_warning("Alchemy")
            
            
            url = f"https://inwritingapi.com/inwriting_public/get_svg.php?tokenID={token_id}"
            nft_data = requests.get(url, stream=True).content.decode('UTF')
            
            p = re.compile(r"<svg xmlns='http://www.w3.org/2000/svg' width='\d+' height='\d+' font-size='24'><style>@import url\('http://fonts.cdnfonts.com/css/menlo'\);</style><text font-family='Menlo' x='0' y='0' xml:space='preserve' text-anchor='start'><tspan x='0' dy='1.208em'>")
            m = p.search(nft_data)
            nft_data = nft_data.replace(m.group(0), '')
            nft_data = nft_data.replace("</tspan><tspan x='0' dy='1.208em'>", '\n')
            nft_data = nft_data.replace("</tspan></text></svg>", '')
            
            
            if nft_data != '':
                if self.print_on_load:
                    title = f"In Writing #{token_id}"
                    self.print_nft_data(nft_data, title)
                    
                self.nft_data_dict['token_id'][token_id] = nft_data
                
                return self.nft_data_dict['token_id'][token_id]
            else:
                self.invalid_param_warning(token_id)
            
        
        return None
    
    # This method requires an Alchemy API
    def get_owned_nfts(self, wallet_address):
        
        if self.ALCHEMY_API_KEY != '':
            method = "getNFTs"
            alchemy_url = f"{self.ALCHEMY_API_URL}/{method}?owner={wallet_address}&contractAddresses%5B%5D={self.INWRITING_CONTRACT}"
            alchemy_data = requests.get(alchemy_url).json()
            owned_nfts = alchemy_data['ownedNfts']
            
            if wallet_address not in self.nft_data_dict['wallet_address'].keys():
                self.nft_data_dict['wallet_address'][wallet_address] = {}
            
            for owned_nft in owned_nfts:
                metadata = owned_nft['metadata']
                if 'string' in metadata.keys():
                    try:
                        nft_data = base64.b64decode(metadata['string']).decode('UTF')
                    except:
                        nft_data = base64.b64decode(metadata['string']).decode('latin')
                
                    if metadata['name'] not in self.nft_data_dict['wallet_address'][wallet_address].keys():
                        self.nft_data_dict['wallet_address'][wallet_address][metadata['name']] = nft_data
                    
                    if self.print_on_load:
                        title = metadata['name']
                        self.print_nft_data(nft_data, title)
                else:
                    self.invalid_param_warning(metadata['name'])
            
            return self.nft_data_dict['wallet_address'][wallet_address]
        else:
            self.missing_api_warning("Alchemy")
        
        return None
    
    # This method requires a Polygonscan API
    def get_nft_by_txhash(self, txhash):
        
        if self.POLYGONSCAN_API_KEY != '':
            pol_transaction_url = f"{self.POLYGONSCAN_API_URL}&module=proxy&action=eth_getTransactionByHash&txhash={txhash}"
            pol_abi_url = f"{self.POLYGONSCAN_API_URL}&module=contract&action=getabi&address={self.INWRITING_CONTRACT}"
            pol_abi_data = requests.get(pol_abi_url).json()
            
            pol_w3 = web3.Web3(web3.Web3.HTTPProvider(pol_transaction_url))
            pol_tx = pol_w3.eth.getTransaction(txhash)
            
            pol_contract = pol_w3.eth.contract(pol_tx['to'], abi=pol_abi_data['result'])
            pol_func_obj, pol_func_params = pol_contract.decode_function_input(pol_tx['input'])
            if 'str' in pol_func_params.keys():
                nft_data = pol_func_params['str']
                
                if self.print_on_load:
                    title = 'Unidentified'
                    self.print_nft_data(nft_data, title)
                
                self.nft_data_dict['txhash'][txhash] = nft_data
                
                return self.nft_data_dict['txhash'][txhash] 
            else:
                self.invalid_param_warning(txhash)
        else:
            self.missing_api_warning("PolygonScan")
        
        return None
    
    
    def print_nft_data(self, nft_data, title):
        print(colors[random.randint(0,len(colors)-1)], end='')
        print("======================")
        print(f'   {title}')
        print("======================")
        #if evaluate == False:
        print(nft_data)
    
    # Warning prompts
    def missing_api_warning(self, api):
        print(f"{Symbol.INVALID_STR} Warning: Api key for {api} has not been specified.")
    def invalid_param_warning(self, parameter=''):
        print(f"{Symbol.INVALID_STR} Warning: NFT data for {parameter} cannot be found.")


# Formatting classes
class Format:
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\u001b[7m'
    END = '\033[0m'
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    WHITE = '\033[37m'
    BRIGHT_WHITE = '\u001b[37;1m'
    GREEN = '\u001b[38;5;71m'
    ROBIN_GREEN = '\u001b[38;5;42m'
    GREY = '\033[90m'
    YELLOW = '\033[33;1m'
    BRIGHT_YELLOW = '\u001b[38;5;229m'
    ORANGE = '\u001b[38;5;208m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    BRIGHT_BLUE = '\033[34;1m'
    BLUE_DREAM = '\033[38;5;75m'
    FAIL = '\033[91m'
    BRIGHT_RED = '\u001b[38;5;216m'
class Symbol:
    ARROW = '\u21B3'
    VALID_STR = f"{Colors.OKBLUE}[+]{Format.END}"
    NEUTRAL_STR = f"{Colors.YELLOW}[~]{Format.END}"
    INVALID_STR = f"{Colors.FAIL}[-]{Format.END}"

# Convert Colors class to dict
colors_dict = dict(vars(Colors))
for key in list(colors_dict.keys()):
    if key.startswith('__'):
        colors_dict.pop(key)
colors = list(colors_dict.values())

# For overwriting lines in stdout
def overwrite_last_line(num_lines=1):
    delete_line_command = "\033[F"*num_lines
    sys.stdout.write(delete_line_command)


if __name__ == '__main__':
    
    PYTHON_HEADER = "#!/usr/bin/env python3"
    
    if len(sys.argv) > 1:
        
        inwriting = InWritingNFTExplorer()
        inwriting.print_on_load = True
        
        evaluate = False; i = 0
        if sys.argv[1] == '-x':
            evaluate = True
            i += 1
        
        if sys.argv[i+1].isdigit():
            nft = inwriting.get_nft_by_token(sys.argv[i+1])
            
            if not (nft is None):
                #print(colors[random.randint(0,len(colors)-1)], end='')
                #print("======================")
                #print('  ',metadata['name'])
                #print("======================")
                ##if evaluate == False:
                #print(nft_data)
                
                if evaluate and nft.startswith(PYTHON_HEADER):
                    warning_prompt = str(input(f"{Symbol.NEUTRAL_STR} Are you sure you want to execute the specified NFT? (y|n): ")).lower()
                    if warning_prompt == 'y':
                        exec(nft)
                        #os.system(f"""python -c '''{nft}'''""")
        else:
            if len(sys.argv) > i+2:
                if sys.argv[i+1] == '-w':
                    inwriting.get_owned_nfts(sys.argv[i+2])
                if sys.argv[i+1] == '-tx':
                    nft = inwriting.get_nft_by_txhash(sys.argv[i+2])
                    if not (nft is None):
                        
                        #print(colors[random.randint(0,len(colors)-1)], end='')
                        #print("======================")
                        #print('  Unresolved Title')
                        #print("======================")
                        ##if evaluate == False:
                        #print(nft_data)
                        
                        if evaluate and nft.startswith(PYTHON_HEADER):
                            warning_prompt = str(input(f"{Symbol.NEUTRAL_STR} Are you sure you want to execute the specified NFT? (y|n): ")).lower()
                            if warning_prompt == 'y':
                                #os.system(f"""python -c '''{nft}'''""")
                                exec(nft)
        
