class Solution {
    public List<Integer> zigzagTraversal(int[][] grid) {
       List<Integer>result=new ArrayList<>();
       int count =0;
       for(int i=0;i<grid.length;i++){
        if(i%2==0){
            for(int j=0;j<grid[i].length;j++){
                if(count%2==0){
                    result.add(grid[i][j]);
                
                }
                count++;
            }
        }else{
            for(int j=grid[i].length-1;j>=0;j--){
                if(count%2==0){
                    result.add(grid[i][j]);
                }
                count++;
            }
        }
       } 
       return result;
    }
}