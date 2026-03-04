"""
PPO Training Script for Delivery Route Optimization
Trains a PPO agent to optimize delivery sequences
"""
import os
import sys
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rl.env import DeliveryEnv, create_random_co2_matrix

# Training configuration
TRAINING_CONFIG = {
    "n_locations": 10,  # Number of delivery locations for training
    "n_training_envs": 4,  # Number of parallel environments
    "total_timesteps": 100000,  # Total training steps
    "learning_rate": 0.0003,
    "n_steps": 2048,
    "batch_size": 64,
    "n_epochs": 10,
    "gamma": 0.99,
    "seed": 42,
    "model_save_path": "rl_models/ppo_delivery_route",
    "checkpoint_freq": 10000
}


def create_training_env(rank: int, seed: int = 0):
    """
    Create a training environment with random CO₂ matrix
    
    Args:
        rank: Environment rank for parallel training
        seed: Base random seed
        
    Returns:
        Environment creation function
    """
    def _init():
        # Create random CO₂ matrix for this environment
        env_seed = seed + rank
        co2_matrix = create_random_co2_matrix(
            n_locations=TRAINING_CONFIG["n_locations"],
            seed=env_seed
        )
        env = DeliveryEnv(co2_matrix=co2_matrix, start_index=0)
        return env
    
    return _init


def train_ppo_agent():
    """
    Train PPO agent for delivery route optimization
    """
    print("=" * 60)
    print("GreenRoute - PPO Training for Route Optimization")
    print("=" * 60)
    
    # Create model directory
    os.makedirs("rl_models", exist_ok=True)
    
    # Set random seeds for reproducibility
    np.random.seed(TRAINING_CONFIG["seed"])
    
    # Create vectorized training environments
    print(f"\nCreating {TRAINING_CONFIG['n_training_envs']} parallel training environments...")
    print(f"   Locations per route: {TRAINING_CONFIG['n_locations']}")
    
    # Create environment functions
    env_fns = [
        create_training_env(rank=i, seed=TRAINING_CONFIG["seed"])
        for i in range(TRAINING_CONFIG["n_training_envs"])
    ]
    
    # Create vectorized training environment
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.monitor import Monitor
    train_env = DummyVecEnv(env_fns)
    
    # Create evaluation environment (wrapped with Monitor to avoid warnings)
    eval_co2_matrix = create_random_co2_matrix(
        n_locations=TRAINING_CONFIG["n_locations"],
        seed=TRAINING_CONFIG["seed"] + 1000
    )
    eval_env = Monitor(DeliveryEnv(co2_matrix=eval_co2_matrix, start_index=0))
    
    # Create callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=TRAINING_CONFIG["checkpoint_freq"],
        save_path="rl_models/checkpoints/",
        name_prefix="ppo_delivery"
    )
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="rl_models/best/",
        log_path="rl_models/logs/",
        eval_freq=5000,
        deterministic=True,
        render=False
    )
    
    # Create PPO model
    print("\nInitialising PPO agent...")
    print(f"   Learning rate: {TRAINING_CONFIG['learning_rate']}")
    print(f"   Batch size: {TRAINING_CONFIG['batch_size']}")
    print(f"   Gamma: {TRAINING_CONFIG['gamma']}")
    
    model = PPO(
        "MlpPolicy",
        train_env,
        learning_rate=TRAINING_CONFIG["learning_rate"],
        n_steps=TRAINING_CONFIG["n_steps"],
        batch_size=TRAINING_CONFIG["batch_size"],
        n_epochs=TRAINING_CONFIG["n_epochs"],
        gamma=TRAINING_CONFIG["gamma"],
        verbose=1,
        seed=TRAINING_CONFIG["seed"]
    )
    
    # Train the model
    print(f"\nStarting training for {TRAINING_CONFIG['total_timesteps']} timesteps...")
    print("   This may take several minutes...")
    print("   Training progress will be shown below:\n")
    
    model.learn(
        total_timesteps=TRAINING_CONFIG["total_timesteps"],
        callback=[checkpoint_callback, eval_callback],
        progress_bar=False  # Disabled to avoid extra dependencies
    )
    
    # Save final model
    final_path = TRAINING_CONFIG["model_save_path"]
    model.save(final_path)
    print(f"\nFinal training complete! Model saved to: {final_path}")
    
    # Cleanup
    train_env.close()
    eval_env.close()
    
    return model


def test_trained_model(model_path: str = None):
    """
    Test the trained model on a sample problem
    
    Args:
        model_path: Path to trained model (default: use training config path)
    """
    if model_path is None:
        model_path = TRAINING_CONFIG["model_save_path"]
    
    print("\n" + "=" * 60)
    print("Testing Trained Model")
    print("=" * 60)
    
    # Load model
    model = PPO.load(model_path)
    
    # Create test environment
    test_co2_matrix = create_random_co2_matrix(
        n_locations=TRAINING_CONFIG["n_locations"],
        seed=9999
    )
    
    env = DeliveryEnv(co2_matrix=test_co2_matrix, start_index=0)
    
    # Run episode
    obs, info = env.reset()
    done = False
    total_reward = 0
    
    print("\nRunning test episode...")
    
    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        done = terminated or truncated
    
    route = env.get_route()
    total_co2 = env.get_total_co2()
    
    print(f"\nTest Results:")
    print(f"   Route: {route}")
    print(f"   Total CO2: {total_co2:.2f} kg")
    print(f"   Total Reward: {total_reward:.2f}")
    
    env.close()


if __name__ == "__main__":
    # Train the model
    model = train_ppo_agent()
    
    # Test the trained model
    test_trained_model()
    
    print("\n" + "=" * 60)
    print("Training and testing complete!")
    print("=" * 60)
