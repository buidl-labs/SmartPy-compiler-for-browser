import smartpy as sp

FA2 = sp.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")

class Offer:
    """
    type offer = {
        key = nat : {
            is_for_sale = boolean,
            seller = address,
            min_sale_value = mutez
        }
    }
    """
    
    def get_value_type():
        return sp.TRecord(
            is_for_sale = sp.TBool,
            seller = sp.TAddress,
            min_sale_value = sp.TMutez
        )
    
    def get_key_type():
        """ Cryptobot Token ID """
        return sp.TNat

class Bid:
    """
    type bid = {
        key = nat : [{
            has_bid = boolean,
            bidder = address,
            bid_value = mutez
        }]
    }
    """
    
    def get_value_type():
        return sp.TList(sp.TRecord(
                has_bid = sp.TBool,
                bidder = sp.TAddress,
                bid_value = sp.TMutez
            ))
    
    def get_key_type():
        """ Cryptobot Token ID """
        return sp.TNat

class Cryptobot(FA2.FA2):
    def __init__(self, config, admin):
        FA2.FA2_core.__init__(self, config, paused = False, administrator = admin,
        offer = sp.map(tkey = Offer.get_key_type(), tvalue = Offer.get_value_type()),
        bid = sp.map(tkey = Bid.get_key_type(), tvalue = Bid.get_value_type())
        )
            
    @sp.entry_point
    def accept_bid_for_bot(self, params):
        # Make sure that sp.sender has admin access otherwise don't proceed forward
        # Make sure that contract isn't paused
        
        sp.set_type(params.token_id, sp.TNat)
        sp.set_type(params.nft_amount, sp.TNat)
        
        # Make sure that the NFT token id is already present in the ledger
        sp.verify(self.token_id_set.contains(self.data.all_tokens, params.token_id), "TOKEN ID NOT FOUND")
        
        # NFT transfer amount should be 1
        sp.verify(params.nft_amount == 1, "NFT AMOUNT OF 1 REQUIRED")
        
        # Make sure that the caller is the owner of NFT token id else throw error 
        user = self.ledger_key.make(sp.sender, params.token_id)
        sp.verify(self.data.ledger.contains(user) == True, "NOT OWNER OF NFT TOKEN ID")
        
        # Make sure their is aleast one bid for NFT token id
        sp.verify(sp.len(self.data.bid[params.token_id]) > 0, "NO BIDDER YET")
        
    
        highest_bidder = sp.local("highest_bidder", sp.record(
                has_bid = False,
                bidder = sp.address("tz1iLVzBpCNTGz6tCBK2KHaQ8o44mmhLTBio"),
                bid_value = sp.mutez(0)
            ))
    
        # transfer the highest bidder value to the seller account    
        sp.for bidder in self.data.bid[params.token_id]:
            # store highest bidder 
            sp.if bidder.bid_value > highest_bidder.value.bid_value:
                highest_bidder.value = bidder
        
        # transfer ownership to the highest bidder account
        from_user = self.ledger_key.make(sp.sender, params.token_id)
        to_user = self.ledger_key.make(highest_bidder.value.bidder, params.token_id)
        
        self.data.ledger[from_user].balance = sp.as_nat(
            self.data.ledger[from_user].balance - params.nft_amount)
            
        sp.if self.data.ledger.contains(to_user):
            self.data.ledger[to_user].balance += params.nft_amount
        sp.else:
             self.data.ledger[to_user] = FA2.Ledger_value.make(params.nft_amount)
        
        # transfer bid amount to seller
        # take out x percentage and send it to admin account
        
        # 10% commission
        commission = sp.split_tokens(highest_bidder.value.bid_value, sp.nat(10), sp.nat(100))
        
        # Transfer xtz to the seller
        sp.send(sp.sender, highest_bidder.value.bid_value - commission)
        
        # Transfer commission to the admin
        sp.send(self.data.administrator, commission)
        
        # return the xtz amount to the rest of the bidders if any
        sp.for bidder in self.data.bid[params.token_id]:
            sp.if bidder.bidder != highest_bidder.value.bidder:
                sp.send(bidder.bidder, bidder.bid_value)
        
        del self.data.offer[params.token_id]
        del self.data.bid[params.token_id]

        
    @sp.entry_point
    def enter_bid_for_bot(self, params):
        #TOOD: HOLD MUTEZ value within the contract
        # Make sure that sp.sender has admin access otherwise don't proceed forward
        # Make sure that contract isn't paused
        
        sp.set_type(params.token_id, sp.TNat)
        # sp.set_type(params.bid_value, sp.TMutez)
        
        # Make sure that the NFT token id is already present in the ledger
        sp.verify(self.token_id_set.contains(self.data.all_tokens, params.token_id), "TOKEN ID NOT FOUND")
        
        # Make sure that NFT token id is listed for bidding
        sp.verify(self.data.offer.contains(params.token_id) == True, "NFT TOKEN ID NOT OPEN FOR BIDDING")
        
        # Make sure NFT token id is up for sale
        sp.verify(self.data.offer[params.token_id].is_for_sale == True, "NFT TOKEN ID IS NOT UP FOR SALE")
        
        # Make sure that bidding amount is more than min_offer_price
        sp.verify(self.data.offer[params.token_id].min_sale_value < sp.amount, "INSUFFICIENT BIDDING VALUE")
        
        # Add user to bidding list for the NFT with the token id
        sp.if self.data.bid.contains(params.token_id):
            self.data.bid[params.token_id].push(sp.record(has_bid = True, bidder = sp.sender, bid_value = sp.amount))
        sp.else:
            self.data.bid[params.token_id] = sp.list([sp.record(has_bid = True, bidder = sp.sender, bid_value = sp.amount)])
        
    
    @sp.entry_point
    def offer_bot_for_sale(self, params):
        # Make sure that sp.sender has admin access otherwise don't proceed forward
        # Make sure that contract isn't paused
        
        sp.set_type(params.token_id, sp.TNat)
        sp.set_type(params.min_sale_price, sp.TMutez)
        
        # Make sure that the NFT token id is already present
        sp.verify(self.token_id_set.contains(self.data.all_tokens, params.token_id), "TOKEN ID NOT FOUND")
        
        # Make user that min_sale_value is more than zero mutez
        sp.verify(params.min_sale_price > sp.mutez(0), "MIN VALUE SHOULD BE MORE THAN ZERO")
        user = self.ledger_key.make(sp.sender, params.token_id)
        
        #Make sure that the caller is the owner of NFT token id else throw error 
        sp.if self.data.ledger.contains(user):
            # Make NFT with token id open for offers
            self.data.offer[params.token_id] = sp.record(is_for_sale = True, seller = sp.sender, min_sale_value = params.min_sale_price)
        sp.else:
            sp.failwith("NOT OWNER OF NFT TOKEN ID")
    
    @sp.entry_point
    def bot_no_longer_for_sale(self, params):
        # Make sure that sp.sender has admin access otherwise don't proceed forward
        # Make sure that contract isn't paused
        
        sp.set_type(params.token_id, sp.TNat)
        
        # Make sure that the NFT token id is already present
        sp.verify(self.token_id_set.contains(self.data.all_tokens, params.token_id), "TOKEN ID NOT FOUND")
        
        user = self.ledger_key.make(sp.sender, params.token_id)
        
        #Make sure that the caller is the owner of NFT token id else throw error 
        sp.if self.data.ledger.contains(user):
            # Remove NFT token id from offers list
            del self.data.offer[params.token_id]
        sp.else:
            sp.failwith("NOT OWNER OF NFT TOKEN ID")
        
        # Return bid amount if any for the token_id to the bidders
        sp.if self.data.bid.contains(params.token_id):
            sp.for bidder in self.data.bid[params.token_id]:
                sp.send(bidder.bidder, bidder.bid_value)
                
            #Remove NFT token id from bid list
            del self.data.bid[params.token_id]
    
    @sp.entry_point
    def widthdraw_bid_for_bot(self, params):
        # Make sure that sp.sender has admin access otherwise don't proceed forward
        # Make sure that contract isn't paused
        
        # Make sure that the NFT token id is already present
        sp.verify(self.token_id_set.contains(self.data.all_tokens, params.token_id), "TOKEN ID NOT FOUND")
        
        # Make sure that NFT token id is listed for bidding
        sp.verify(self.data.bid.contains(params.token_id) == True, "NFT TOKEN ID NOT OPEN FOR BIDDING")
        
        # Check that sp.sender is a bidder
        sp.if self.data.bid.contains(params.token_id):
            sp.for bidder in self.data.bid[params.token_id]:
                sp.if bidder.bidder == sp.sender:
                    # Refund the bid value
                    sp.send(bidder.bidder, bidder.bid_value)
                    bidder.bid_value = sp.mutez(0)
                    bidder.has_bid = False
            

    @sp.entry_point
    def mint(self, params):
        sp.verify(sp.sender == self.data.administrator)
        
        if self.config.non_fungible:
            sp.verify(params.amount == 1, "NFT-asset: amount <> 1")
            sp.verify(~ self.token_id_set.contains(self.data.all_tokens, params.token_id), "NFT-asset: cannon mint the same token twice")
        
        user = self.ledger_key.make(params.address, params.token_id)
        self.token_id_set.add(self.data.all_tokens, params.token_id)
        sp.if self.data.ledger.contains(user):
            self.data.ledger[user].balance += params.amount
        sp.else:
            self.data.ledger[user] = FA2.Ledger_value.make(params.amount)
        
        sp.if self.data.tokens.contains(params.token_id):
            pass
        sp.else:
            self.data.tokens[params.token_id] = sp.record(
                    token_id = params.token_id,
                    symbol = params.symbol,
                    name = "", 
                    decimals = 0,
                    extras = params.extras
                )
            

@sp.add_test(name = "Cryptobot")
def test():
    scenario = sp.test_scenario()
    
    admin = sp.address("tz1XP2AUZAaCbi1PCNQ7pEdMS1EEjL4p4YPY")
    
    mark = sp.test_account("Mark")
    elon = sp.test_account("Mars")
    alice = sp.test_account("alice")
    
    # (1) Initialize Cryptobot as `cryptobot` with non_fungible set to True.
    # (2) Add it to the scenario.
    cryptobot = Cryptobot(FA2.FA2_config(non_fungible = True), admin)
    scenario += cryptobot
    
    # Mint 1 token to mark with symbol - "CTB", amount - 1, token_id - 0 and extras - {"value": "First bot"}
    scenario += cryptobot.mint(address = mark.address, 
                            amount = 1,
                            symbol = 'CTB',
                            token_id = 5,
                            extras = { "value": "4th bot"}).run(sender = admin)
    # Mint 1 token to mark with symbol - "CTB", amount - 1, token_id - 1 and extras - {"value": "Second bot"}                           
    scenario += cryptobot.mint(address = elon.address,
                            amount = 1,
                            symbol = 'CTB',
                            token_id = 6,
                            extras = { "value": "Second bot" }).run(sender = admin)
    
    scenario += cryptobot.offer_bot_for_sale(token_id = 6, min_sale_price = sp.mutez(1000)).run(sender = elon)
    
    # scenario += cryptobot.bot_no_longer_for_sale(token_id = 6).run(sender = elon)
    scenario += cryptobot.enter_bid_for_bot(token_id = 6).run(sender = mark, amount = sp.mutez(10000000))
    scenario += cryptobot.enter_bid_for_bot(token_id = 6).run(sender = alice, amount = sp.mutez(12000000))
    scenario += cryptobot.widthdraw_bid_for_bot(token_id = 6).run(sender = alice)
    scenario += cryptobot.accept_bid_for_bot(token_id = 6, nft_amount = 1).run(sender = elon)