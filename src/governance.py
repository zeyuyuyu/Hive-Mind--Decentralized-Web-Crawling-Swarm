from typing import Dict, List
import math
from datetime import datetime, timedelta

class Proposal:
    def __init__(self, id: str, title: str, description: str, author: str, funding_requested: float):
        self.id = id
        self.title = title
        self.description = description
        self.author = author
        self.funding_requested = funding_requested
        self.votes = {}
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(days=7)
        self.status = 'active'

class GovernanceSystem:
    def __init__(self):
        self.proposals: Dict[str, Proposal] = {}
        self.token_balances: Dict[str, float] = {}
        self.matching_pool: float = 0
    
    def create_proposal(self, id: str, title: str, description: str, author: str, funding: float) -> Proposal:
        if id in self.proposals:
            raise ValueError('Proposal ID already exists')
            
        proposal = Proposal(id, title, description, author, funding)
        self.proposals[id] = proposal
        return proposal
    
    def vote(self, proposal_id: str, voter: str, token_amount: float) -> bool:
        if proposal_id not in self.proposals:
            raise ValueError('Invalid proposal ID')
            
        if self.token_balances.get(voter, 0) < token_amount:
            raise ValueError('Insufficient token balance')
            
        proposal = self.proposals[proposal_id]
        
        if proposal.status != 'active' or datetime.now() > proposal.expires_at:
            raise ValueError('Proposal is not active')
            
        # Quadratic voting - square root of tokens committed
        voting_power = math.sqrt(token_amount)
        proposal.votes[voter] = voting_power
        
        # Deduct tokens
        self.token_balances[voter] -= token_amount
        return True
        
    def calculate_quadratic_funding(self, proposal_id: str) -> float:
        if proposal_id not in self.proposals:
            raise ValueError('Invalid proposal ID')
            
        proposal = self.proposals[proposal_id]
        
        if proposal.status != 'active':
            raise ValueError('Proposal must be active')
            
        # Sum of square roots of contributions
        sum_sqrt_contributions = sum(proposal.votes.values())
        
        # Square of sum of square roots
        funding = (sum_sqrt_contributions ** 2)
        
        # Scale by matching pool ratio
        total_funding = min(funding, self.matching_pool)
        return total_funding
    
    def finalize_proposal(self, proposal_id: str) -> Dict:
        if proposal_id not in self.proposals:
            raise ValueError('Invalid proposal ID')
            
        proposal = self.proposals[proposal_id]
        
        if datetime.now() < proposal.expires_at:
            raise ValueError('Proposal voting period not ended')
            
        funding = self.calculate_quadratic_funding(proposal_id)
        proposal.status = 'completed'
        
        return {
            'proposal_id': proposal_id,
            'total_votes': len(proposal.votes),
            'funding_awarded': funding,
            'status': proposal.status
        }
    
    def add_matching_funds(self, amount: float):
        self.matching_pool += amount
        
    def get_proposal_status(self, proposal_id: str) -> Dict:
        if proposal_id not in self.proposals:
            raise ValueError('Invalid proposal ID')
            
        proposal = self.proposals[proposal_id]
        return {
            'id': proposal.id,
            'title': proposal.title,
            'author': proposal.author,
            'status': proposal.status,
            'votes': len(proposal.votes),
            'funding_requested': proposal.funding_requested,
            'expires_at': proposal.expires_at
        }