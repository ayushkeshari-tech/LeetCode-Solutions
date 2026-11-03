class Solution {
    public int minBitFlips(int start, int goal) {
        int diff = start ^ goal;      
        return Integer.bitCount(diff);    
    }
} 