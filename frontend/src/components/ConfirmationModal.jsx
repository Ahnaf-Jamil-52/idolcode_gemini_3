import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';

export const ConfirmationModal = ({ isOpen, onClose, onConfirm, coderHandle, isChange = false }) => {
  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent className="glass-card border-2 border-primary/30">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-2xl bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
            {isChange ? 'Change Coding Idol' : 'Select Coding Idol'}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-base text-muted-foreground pt-2">
            {isChange ? (
              <>Change your coding idol to <span className="text-primary font-semibold">{coderHandle}</span>?</>
            ) : (
              <>Select <span className="text-primary font-semibold">{coderHandle}</span> as coding idol?</>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel className="hover:bg-secondary">
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction 
            onClick={onConfirm}
            className="bg-gradient-to-r from-primary to-accent hover:shadow-[0_0_20px_rgba(6,182,212,0.5)] hover:scale-105 transition-all"
          >
            {isChange ? 'Change' : 'Confirm'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default ConfirmationModal;
