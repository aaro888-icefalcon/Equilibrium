# Combat Turn Prompt

Register: {register_directive}
Round {round}: {actor} uses {action_type}.
Result: {action_result}
Damage dealt: {damage_dealt}. Status applied: {status_applied}.
Enemies remaining: {enemies_remaining}.
Player condition: {player_condition}

## Format Contract
25-60 words. Prose only. No menu, no choices. Damage and status effects are rendered by the runtime.

## Instructions
Narrate this combat moment. Do not invent powers not in the payload. Do not resolve outcomes the player did not choose.
