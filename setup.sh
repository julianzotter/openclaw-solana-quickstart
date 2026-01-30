#!/bin/bash

set -e

echo "🚀 OpenClaw Solana Trading Setup"
echo "================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Node.js is installed
echo "📦 Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    echo "Please install Node.js 22+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2)
echo -e "${GREEN}✅ Node.js ${NODE_VERSION} found${NC}"
echo

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found${NC}"
    echo "Please install npm (usually comes with Node.js)"
    exit 1
fi

# Check if OpenClaw is installed
echo "🔧 Checking OpenClaw installation..."
if ! command -v openclaw &> /dev/null; then
    echo -e "${YELLOW}⚠️  OpenClaw not found. Installing...${NC}"
    npm install -g openclaw
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ OpenClaw installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install OpenClaw${NC}"
        echo "Try running: npm install -g openclaw"
        exit 1
    fi
else
    echo -e "${GREEN}✅ OpenClaw already installed${NC}"
fi
echo

# Create OpenClaw workspace directory if it doesn't exist
WORKSPACE_DIR="$HOME/.openclaw/workspace"
echo "📁 Setting up workspace at ${WORKSPACE_DIR}..."
mkdir -p "$WORKSPACE_DIR"

# Generate Solana keypair
echo "🔑 Generating Solana wallet keypair..."
WALLET_FILE="$WORKSPACE_DIR/solana-wallet.json"

if [ -f "$WALLET_FILE" ]; then
    echo -e "${YELLOW}⚠️  Wallet already exists at ${WALLET_FILE}${NC}"
    echo "Using existing wallet..."
else
    # Create a simple Node.js script to generate the keypair
    cat > /tmp/generate-keypair.js << 'EOF'
const { Keypair } = require('@solana/web3.js');
const fs = require('fs');

// Generate new keypair
const keypair = Keypair.generate();

// Create the wallet file format
const walletData = Array.from(keypair.secretKey);

// Write to file
const walletPath = process.argv[2];
fs.writeFileSync(walletPath, JSON.stringify(walletData, null, 2));

console.log('Keypair generated and saved to:', walletPath);
console.log('Public key (wallet address):', keypair.publicKey.toString());
EOF

    # Install @solana/web3.js if not available in current directory
    if [ ! -d "node_modules/@solana/web3.js" ]; then
        echo "Installing @solana/web3.js..."
        npm install @solana/web3.js
    fi

    # Generate the keypair
    node /tmp/generate-keypair.js "$WALLET_FILE"
    
    # Clean up temp file
    rm /tmp/generate-keypair.js
fi

# Extract and display the public key
echo
echo "🎯 Extracting wallet address..."
PUBLIC_KEY=$(node -e "
const fs = require('fs');
const { Keypair } = require('@solana/web3.js');
const secretKey = new Uint8Array(JSON.parse(fs.readFileSync('$WALLET_FILE', 'utf8')));
const keypair = Keypair.fromSecretKey(secretKey);
console.log(keypair.publicKey.toString());
")

echo
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo
echo -e "${YELLOW}📍 Your agent's wallet address:${NC}"
echo -e "${GREEN}${PUBLIC_KEY}${NC}"
echo
echo -e "${YELLOW}💰 Fund this address with:${NC}"
echo "• 0.1 SOL (for transaction fees)"
echo "• \$50 USDC (for trading)"
echo
echo -e "${YELLOW}📁 Wallet saved to:${NC}"
echo "$WALLET_FILE"
echo
echo -e "${YELLOW}🚀 Next steps:${NC}"
echo "1. Fund your wallet address (shown above)"
echo "2. Run: ./fund-wallet.sh (to check funding status)"
echo "3. Run: cd trading && npm install && node monitor.js"
echo

# Check if Solana CLI is available and configure it
if command -v solana &> /dev/null; then
    echo -e "${GREEN}✅ Solana CLI detected - configuring...${NC}"
    solana config set --keypair "$WALLET_FILE" --url https://api.mainnet-beta.solana.com
    echo "Solana CLI configured to use your agent's wallet"
    echo
fi

echo -e "${GREEN}🎉 Your OpenClaw Solana agent is ready to be funded!${NC}"