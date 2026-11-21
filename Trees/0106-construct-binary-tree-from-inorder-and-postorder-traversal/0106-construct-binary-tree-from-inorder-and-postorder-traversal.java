/**
 * Definition for a binary tree node.
 * public class TreeNode {
 *     int val;
 *     TreeNode left;
 *     TreeNode right;
 *     TreeNode() {}
 *     TreeNode(int val) { this.val = val; }
 *     TreeNode(int val, TreeNode left, TreeNode right) {
 *         this.val = val;
 *         this.left = left;
 *         this.right = right;
 *     }
 * }
 */
class Solution {
    int postIndex;
    Map<Integer,Integer>map=new HashMap<>();
    public TreeNode buildTree(int[] inorder, int[] postorder) {
        postIndex=postorder.length-1;
        for(int i=0;i<inorder.length;i++){
             map.put(inorder[i],i);
             }
             return solve(inorder,postorder,0,inorder.length-1);
        }
        public TreeNode solve(int[] inorder,int[] postorder,int start,int end){
            if(start>end){
                return null;
            }
            int value=postorder[postIndex--];
            TreeNode root=new TreeNode(value);
            int index=map.get(value);
            root.right=solve(inorder,postorder,index+1,end);
            root.left=solve(inorder,postorder,start,index-1);
            return root;
        }
}
    